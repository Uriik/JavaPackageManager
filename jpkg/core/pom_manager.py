import os
import shutil
import time
from lxml import etree

class PomManager:
    def __init__(self, pom_path: str):
        """
        Carrega o arquivo pom.xml preservando comentários e formatação.
        """
        self.pom_path = os.path.abspath(pom_path)
        if not os.path.exists(self.pom_path):
            raise FileNotFoundError(f"Arquivo pom.xml não encontrado em: {self.pom_path}")
            
        # Parser que mantém comentários e espaços em branco originais
        self.parser = etree.XMLParser(remove_blank_text=False, resolve_entities=False)
        self.tree = etree.parse(self.pom_path, self.parser)
        self.root = self.tree.getroot()
        
        # Detectar namespace Maven (geralmente http://maven.apache.org/POM/4.0.0)
        self.ns = self.root.nsmap.get(None)
        self.nsmap = self.root.nsmap.copy()
        
    def _tag(self, name: str) -> str:
        """Helper para retornar a tag formatada com o namespace detectado."""
        return f"{{{self.ns}}}{name}" if self.ns else name

    def _find_element(self, path: str):
        """Busca um elemento usando XPath considerando o namespace Maven se existir."""
        if self.ns:
            # Substitui nomes de tags por nomes com prefixo ns: no XPath
            # Ex: 'dependencies/dependency' -> 'ns:dependencies/ns:dependency'
            parts = path.split('/')
            ns_path = '/'.join(f"ns:{p}" if p else "" for p in parts)
            namespaces = {'ns': self.ns}
            return self.root.xpath(ns_path, namespaces=namespaces)
        else:
            return self.root.xpath(path)

    def get_dependencies(self) -> list[dict]:
        """
        Retorna a lista de dependências atuais no pom.xml.
        Formato: [{"groupId": "...", "artifactId": "...", "version": "...", "scope": "..."}]
        """
        dependencies = []
        # Localiza o bloco <dependencies>
        deps_blocks = self._find_element("dependencies")
        if not deps_blocks:
            return dependencies
            
        deps_block = deps_blocks[0]
        
        # Localiza cada <dependency> dentro do bloco
        dep_elements = deps_block.findall(self._tag("dependency"))
        for dep in dep_elements:
            group_el = dep.find(self._tag("groupId"))
            artifact_el = dep.find(self._tag("artifactId"))
            version_el = dep.find(self._tag("version"))
            scope_el = dep.find(self._tag("scope"))
            
            if group_el is not None and artifact_el is not None:
                dependencies.append({
                    "groupId": group_el.text.strip() if group_el.text else "",
                    "artifactId": artifact_el.text.strip() if group_el.text else "",
                    "version": version_el.text.strip() if (version_el is not None and version_el.text) else "",
                    "scope": scope_el.text.strip() if (scope_el is not None and scope_el.text) else "compile"
                })
                
        return dependencies

    def get_project_info(self) -> dict:
        """
        Retorna as informações do projeto do pom.xml (groupId, artifactId, version).
        Resolve groupId/version herdados do parent se necessário.
        """
        g = self.root.find(self._tag("groupId"))
        if g is None:
            parent = self.root.find(self._tag("parent"))
            if parent is not None:
                g = parent.find(self._tag("groupId"))
        
        a = self.root.find(self._tag("artifactId"))
        
        v = self.root.find(self._tag("version"))
        if v is None:
            parent = self.root.find(self._tag("parent"))
            if parent is not None:
                v = parent.find(self._tag("version"))
                
        return {
            "groupId": g.text.strip() if (g is not None and g.text) else "",
            "artifactId": a.text.strip() if (a is not None and a.text) else "",
            "version": v.text.strip() if (v is not None and v.text) else ""
        }


    def _get_or_create_dependencies_block(self):
        """Busca ou cria o elemento <dependencies> com formatação correta."""
        blocks = self._find_element("dependencies")
        if blocks:
            return blocks[0]
            
        # Detectar indentação padrão (geralmente 4 espaços)
        indent = "    "
        # Tenta descobrir indentação observando outros filhos diretos da raiz
        for child in self.root:
            if child.tail and child.tail.startswith("\n"):
                whitespace = child.tail.replace("\n", "")
                if whitespace:
                    indent = whitespace
                    break
                    
        # Criar elemento dependencies
        deps_el = etree.Element(self._tag("dependencies"), nsmap=self.nsmap)
        
        # Definir a indentação de fechamento da tag </dependencies>
        deps_el.tail = "\n" + indent
        
        # Inserir no local ideal (antes do bloco <build>, ou logo antes do fechamento da raiz)
        build_blocks = self._find_element("build")
        if build_blocks:
            build_index = self.root.index(build_blocks[0])
            # Ajustar espaços
            deps_el.text = "\n" + indent
            self.root.insert(build_index, deps_el)
            # Corrigir tail do elemento anterior
            if build_index > 0:
                self.root[build_index - 1].tail = "\n" + indent + "    "
        else:
            # Insere no final
            if len(self.root) > 0:
                last_child = self.root[-1]
                # Modifica o espaçamento do último elemento
                last_child.tail = "\n" + indent
            deps_el.text = "\n" + indent
            self.root.append(deps_el)
            
        return deps_el

    def add_dependency(self, group_id: str, artifact_id: str, version: str, scope: str = "compile"):
        """
        Adiciona uma nova dependência ao pom.xml.
        Se já existir, atualiza a versão.
        """
        # Limpar entradas
        group_id = group_id.strip()
        artifact_id = artifact_id.strip()
        version = version.strip() if version else ""
        scope = scope.strip().lower() if scope else "compile"
        
        # 1. Verificar se já existe no arquivo
        deps_blocks = self._find_element("dependencies")
        if deps_blocks:
            deps_block = deps_blocks[0]
            for dep in deps_block.findall(self._tag("dependency")):
                g = dep.find(self._tag("groupId"))
                a = dep.find(self._tag("artifactId"))
                if g is not None and a is not None and g.text.strip() == group_id and a.text.strip() == artifact_id:
                    # Já existe, apenas atualiza a versão
                    self.update_version(group_id, artifact_id, version)
                    # E o scope, se for diferente de compile
                    v_scope = dep.find(self._tag("scope"))
                    if scope != "compile":
                        if v_scope is not None:
                            v_scope.text = scope
                        else:
                            # Adicionar elemento scope
                            indent_level = "            "
                            v_scope = etree.Element(self._tag("scope"), nsmap=self.nsmap)
                            v_scope.text = scope
                            v_scope.tail = "\n" + "        "
                            # Insere antes do fechamento
                            dep.append(v_scope)
                    elif v_scope is not None:
                        # Se o novo escopo for 'compile' (padrão) e havia um tag de escopo, removemos
                        dep.remove(v_scope)
                    return
                    
        # 2. Criar ou buscar o bloco <dependencies>
        deps_block = self._get_or_create_dependencies_block()
        
        # 3. Detectar a indentação para criar o novo elemento
        # Default: 4 espaços para project, 8 para dependency, 12 para groupId etc.
        indent_deps = "    "
        indent_dep = "        "
        indent_sub = "            "
        
        # Criar a tag <dependency>
        dep_el = etree.Element(self._tag("dependency"), nsmap=self.nsmap)
        dep_el.text = "\n" + indent_sub
        dep_el.tail = "\n" + indent_dep
        
        # Adicionar groupId
        g_el = etree.SubElement(dep_el, self._tag("groupId"))
        g_el.text = group_id
        g_el.tail = "\n" + indent_sub
        
        # Adicionar artifactId
        a_el = etree.SubElement(dep_el, self._tag("artifactId"))
        a_el.text = artifact_id
        a_el.tail = "\n" + indent_sub if (version or scope != "compile") else "\n" + indent_dep
        
        # Adicionar version se informada
        if version:
            v_el = etree.SubElement(dep_el, self._tag("version"))
            v_el.text = version
            v_el.tail = "\n" + indent_sub if scope != "compile" else "\n" + indent_dep
            
        # Adicionar scope se não for compile (escopo padrão que pode ser omitido no Maven)
        if scope and scope != "compile":
            s_el = etree.SubElement(dep_el, self._tag("scope"))
            s_el.text = scope
            s_el.tail = "\n" + indent_dep
            
        # Inserir no bloco <dependencies>
        if len(deps_block) > 0:
            # Já existem dependências, insere no fim com formatação
            last_dep = deps_block[-1]
            last_dep.tail = "\n" + indent_dep
            deps_block.append(dep_el)
        else:
            # Primeira dependência
            deps_block.text = "\n" + indent_dep
            deps_block.append(dep_el)
            
        # Ajustar o tail da última dependência para que o fechamento </dependencies> fique na linha certa
        dep_el.tail = "\n" + indent_deps

    def remove_dependency(self, group_id: str, artifact_id: str) -> bool:
        """
        Remove uma dependência do pom.xml.
        Retorna True se removeu, False caso não tenha encontrado.
        """
        group_id = group_id.strip()
        artifact_id = artifact_id.strip()
        
        deps_blocks = self._find_element("dependencies")
        if not deps_blocks:
            return False
            
        deps_block = deps_blocks[0]
        dep_to_remove = None
        
        for dep in deps_block.findall(self._tag("dependency")):
            g = dep.find(self._tag("groupId"))
            a = dep.find(self._tag("artifactId"))
            if g is not None and a is not None and g.text.strip() == group_id and a.text.strip() == artifact_id:
                dep_to_remove = dep
                break
                
        if dep_to_remove is not None:
            # Se for a última dependência, limpar o bloco
            deps_block.remove(dep_to_remove)
            
            # Se o bloco de dependências ficou vazio, removemos todo o bloco <dependencies>
            if len(deps_block) == 0:
                parent = deps_block.getparent()
                parent.remove(deps_block)
            else:
                # Caso contrário, ajusta o tail do novo último elemento
                last_dep = deps_block[-1]
                last_dep.tail = "\n" + "    " # indent_deps
            return True
            
        return False

    def update_version(self, group_id: str, artifact_id: str, new_version: str) -> bool:
        """
        Atualiza a versão de uma dependência existente.
        Retorna True se atualizou, False caso não tenha encontrado.
        """
        group_id = group_id.strip()
        artifact_id = artifact_id.strip()
        new_version = new_version.strip()
        
        deps_blocks = self._find_element("dependencies")
        if not deps_blocks:
            return False
            
        deps_block = deps_blocks[0]
        for dep in deps_block.findall(self._tag("dependency")):
            g = dep.find(self._tag("groupId"))
            a = dep.find(self._tag("artifactId"))
            if g is not None and a is not None and g.text.strip() == group_id and a.text.strip() == artifact_id:
                v_el = dep.find(self._tag("version"))
                if v_el is not None:
                    if new_version:
                        v_el.text = new_version
                    else:
                        # Se a nova versão for vazia, remove o elemento versão
                        dep.remove(v_el)
                elif new_version:
                    # Criar elemento versão
                    indent_sub = "            "
                    v_el = etree.Element(self._tag("version"), nsmap=self.nsmap)
                    v_el.text = new_version
                    
                    # Insere depois do artifactId
                    a_el = dep.find(self._tag("artifactId"))
                    a_index = dep.index(a_el)
                    
                    # Define tail e insere
                    v_el.tail = a_el.tail
                    a_el.tail = "\n" + indent_sub
                    dep.insert(a_index + 1, v_el)
                return True
                
        return False

    def backup(self) -> str:
        """
        Cria uma cópia de backup do pom.xml.
        """
        backup_path = f"{self.pom_path}.{int(time.time())}.bak"
        shutil.copy2(self.pom_path, backup_path)
        return backup_path

    def save(self):
        """
        Salva as alterações mantendo a formatação e a declaração XML original.
        """
        # Salva o arquivo preservando a declaração XML no topo
        # Ex: <?xml version="1.0" encoding="UTF-8"?>
        self.tree.write(
            self.pom_path,
            xml_declaration=True,
            encoding="utf-8",
            pretty_print=False
        )
