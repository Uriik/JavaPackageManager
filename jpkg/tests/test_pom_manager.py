import os
import tempfile
import pytest
from lxml import etree
from jpkg.core.pom_manager import PomManager

# Conteúdo de um pom.xml de exemplo para testes
TEST_POM_CONTENT = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <groupId>com.example</groupId>
    <artifactId>test-project</artifactId>
    <version>1.0-SNAPSHOT</version>

    <!-- Comentário inicial -->
    <properties>
        <maven.compiler.source>17</maven.compiler.source>
        <maven.compiler.target>17</maven.compiler.target>
    </properties>

    <dependencies>
        <!-- JUnit para testes -->
        <dependency>
            <groupId>org.junit.jupiter</groupId>
            <artifactId>junit-jupiter</artifactId>
            <version>5.8.2</version>
            <scope>test</scope>
        </dependency>
    </dependencies>
</project>
"""

@pytest.fixture
def temp_pom():
    """Cria um arquivo pom.xml temporário para testes."""
    fd, path = tempfile.mkstemp(suffix="-pom.xml")
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(TEST_POM_CONTENT)
        yield path
    finally:
        if os.path.exists(path):
            os.remove(path)
            
@pytest.fixture
def temp_pom_no_deps():
    """Cria um arquivo pom.xml temporário sem o bloco <dependencies>."""
    fd, path = tempfile.mkstemp(suffix="-pom.xml")
    content = TEST_POM_CONTENT.split("<dependencies>")[0] + "</project>"
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(content)
        yield path
    finally:
        if os.path.exists(path):
            os.remove(path)

def test_get_dependencies(temp_pom):
    manager = PomManager(temp_pom)
    deps = manager.get_dependencies()
    
    assert len(deps) == 1
    assert deps[0]["groupId"] == "org.junit.jupiter"
    assert deps[0]["artifactId"] == "junit-jupiter"
    assert deps[0]["version"] == "5.8.2"
    assert deps[0]["scope"] == "test"

def test_add_dependency(temp_pom):
    manager = PomManager(temp_pom)
    manager.add_dependency("org.mockito", "mockito-core", "4.3.1", "test")
    manager.save()
    
    # Recarregar e verificar
    new_manager = PomManager(temp_pom)
    deps = new_manager.get_dependencies()
    
    assert len(deps) == 2
    assert deps[1]["groupId"] == "org.mockito"
    assert deps[1]["artifactId"] == "mockito-core"
    assert deps[1]["version"] == "4.3.1"
    assert deps[1]["scope"] == "test"
    
    # Verificar se o comentário inicial do JUnit ainda está lá
    with open(temp_pom, 'r', encoding='utf-8') as f:
        content = f.read()
        assert "<!-- JUnit para testes -->" in content
        assert "<!-- Comentário inicial -->" in content

def test_add_dependency_to_no_deps_pom(temp_pom_no_deps):
    manager = PomManager(temp_pom_no_deps)
    assert len(manager.get_dependencies()) == 0
    
    manager.add_dependency("org.slf4j", "slf4j-api", "1.7.36")
    manager.save()
    
    # Recarregar e verificar
    new_manager = PomManager(temp_pom_no_deps)
    deps = new_manager.get_dependencies()
    assert len(deps) == 1
    assert deps[0]["groupId"] == "org.slf4j"
    assert deps[0]["artifactId"] == "slf4j-api"
    assert deps[0]["version"] == "1.7.36"
    assert deps[0]["scope"] == "compile" # Padrão assumido

def test_remove_dependency(temp_pom):
    manager = PomManager(temp_pom)
    removed = manager.remove_dependency("org.junit.jupiter", "junit-jupiter")
    assert removed is True
    manager.save()
    
    new_manager = PomManager(temp_pom)
    assert len(new_manager.get_dependencies()) == 0

def test_update_version(temp_pom):
    manager = PomManager(temp_pom)
    updated = manager.update_version("org.junit.jupiter", "junit-jupiter", "5.9.0")
    assert updated is True
    manager.save()
    
    new_manager = PomManager(temp_pom)
    deps = new_manager.get_dependencies()
    assert deps[0]["version"] == "5.9.0"
