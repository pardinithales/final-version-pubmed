import os
import sys
from pathlib import Path
import pyperclip


def gerar_conteudo_para_clipboard(diretorio_origem, max_file_size_kb=100, incluir_conteudo=True):
    """
    Gera uma representação de texto da estrutura de diretórios e conteúdo de arquivos
    para ser copiada para a área de transferência.
    
    Args:
        diretorio_origem (str): Caminho do diretório de origem
        max_file_size_kb (int): Tamanho máximo do arquivo em KB para incluir conteúdo
        incluir_conteudo (bool): Se deve incluir o conteúdo dos arquivos
    
    Returns:
        str: Representação textual da estrutura e conteúdo dos arquivos
    """
    resultado = []
    
    # Extensões permitidas
    extensoes_permitidas = ['.py', '.env', '.txt', '.gitignore']
    
    # Diretórios a ignorar
    dirs_ignorar = ['venv', 'venv311', '__pycache__', '.git', '.idea', '.vscode', 'node_modules']
    
    # Lista para armazenar todos os caminhos
    todos_caminhos = []

    # Função para coletar todos os caminhos
    for root, dirs, files in os.walk(diretorio_origem):
        # Filtrar diretórios a ignorar
        dirs[:] = [d for d in dirs if d not in dirs_ignorar]
        
        # Adicionar o diretório atual
        todos_caminhos.append(root)
        
        # Adicionar todos os arquivos no diretório atual
        for file in files:
            # Verificar se a extensão é permitida
            ext = os.path.splitext(file)[1].lower()
            if ext in extensoes_permitidas or '.gitignore' in file:
                caminho_arquivo = os.path.join(root, file)
                todos_caminhos.append(caminho_arquivo)
    
    # Ordenar os caminhos
    todos_caminhos.sort()
    
    # Primeiro, listar todos os diretórios e arquivos com caminho completo
    for caminho in todos_caminhos:
        resultado.append(caminho)
    
    # Adicionar uma linha em branco para separar
    resultado.append("")
    resultado.append("__")
    resultado.append("")
    
    # Agora, mostrar o conteúdo dos arquivos com o caminho como comentário
    if incluir_conteudo:
        for caminho in todos_caminhos:
            if os.path.isfile(caminho):
                # Verificar o tamanho do arquivo
                tamanho_arquivo_kb = os.path.getsize(caminho) / 1024
                if tamanho_arquivo_kb > max_file_size_kb:
                    resultado.append(f"# {caminho}")
                    resultado.append(f"# [Arquivo muito grande: {tamanho_arquivo_kb:.2f} KB - conteúdo omitido]")
                    resultado.append("")
                    continue
                
                extensao = Path(caminho).suffix.lower()
                if extensao in extensoes_permitidas or '.gitignore' in caminho:
                    # Adicionar caminho como comentário
                    resultado.append(f"# {caminho}")
                    
                    # Ler e adicionar o conteúdo do arquivo
                    try:
                        with open(caminho, 'r', encoding='utf-8', errors='replace') as f:
                            conteudo = f.read()
                            resultado.append(conteudo)
                            resultado.append("")  # Linha em branco após o conteúdo
                    except Exception as e:
                        resultado.append(f"⚠️ Erro ao ler o arquivo: {e}")
                        resultado.append("")

    return "\n".join(resultado)


if __name__ == "__main__":
    # Verificar argumentos de linha de comando
    if len(sys.argv) >= 2:
        diretorio_origem = sys.argv[1]
    else:
        # Usar diretório atual como origem
        diretorio_origem = os.getcwd()
    
    # Limitar tamanho de arquivo a 100KB por padrão
    max_file_size_kb = 100
    
    # Opção para incluir conteúdo (padrão: True)
    incluir_conteudo = True
    
    # Processar argumentos adicionais
    for arg in sys.argv[2:]:
        if arg.startswith('--max-size='):
            try:
                max_file_size_kb = int(arg.split('=')[1])
            except (ValueError, IndexError):
                pass
        elif arg == '--no-content':
            incluir_conteudo = False

    # Exibir informação
    print(f"Gerando representação do diretório: {diretorio_origem}")
    print(f"Tamanho máximo de arquivo: {max_file_size_kb} KB")
    print(f"Incluir conteúdo: {'Sim' if incluir_conteudo else 'Não'}")

    try:
        # Gerar o conteúdo
        conteudo = gerar_conteudo_para_clipboard(diretorio_origem, max_file_size_kb, incluir_conteudo)

        # Copiar para a área de transferência
        pyperclip.copy(conteudo)

        print(f"Conteúdo copiado para a área de transferência!")
        print(f"Total de caracteres: {len(conteudo)}")

    except ImportError:
        print("Erro: Biblioteca 'pyperclip' não encontrada.")
        print("Por favor, instale usando: pip install pyperclip")
        sys.exit(1)
    except Exception as e:
        print(f"Erro ao processar ou copiar o conteúdo: {e}")
        sys.exit(1)
