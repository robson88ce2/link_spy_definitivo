#!/usr/bin/env python3
"""
Script para gerar chaves secretas necessárias para o sistema
Execute este script antes de iniciar o sistema pela primeira vez
"""
import secrets
from cryptography.fernet import Fernet


def gerar_chaves():
    """Gera e exibe as chaves necessárias para o sistema"""
    
    print("=" * 80)
    print("🔐 GERADOR DE CHAVES SECRETAS - Sistema de Rastreamento")
    print("=" * 80)
    print()
    
    # Secret Key para Flask
    secret_key = secrets.token_hex(32)
    print("✅ SECRET_KEY (Flask Sessions):")
    print(f"   {secret_key}")
    print()
    
    # Encryption Key para dados sensíveis
    encryption_key = Fernet.generate_key().decode()
    print("✅ ENCRYPTION_KEY (Criptografia de dados):")
    print(f"   {encryption_key}")
    print()
    
    print("=" * 80)
    print("📝 INSTRUÇÕES:")
    print("=" * 80)
    print()
    print("1. Copie o arquivo .env.example para .env:")
    print("   $ cp .env.example .env")
    print()
    print("2. Abra o arquivo .env e cole as chaves geradas acima:")
    print("   SECRET_KEY=<cole aqui a SECRET_KEY>")
    print("   ENCRYPTION_KEY=<cole aqui a ENCRYPTION_KEY>")
    print()
    print("3. Configure uma senha forte para o admin:")
    print("   ADMIN_PASSWORD=<sua_senha_forte_aqui>")
    print()
    print("4. NUNCA commite o arquivo .env no Git!")
    print("   (Ele já está no .gitignore)")
    print()
    print("⚠️  IMPORTANTE: Guarde estas chaves em local seguro!")
    print("    Se perdê-las, não será possível descriptografar dados antigos.")
    print()
    print("=" * 80)


if __name__ == "__main__":
    try:
        gerar_chaves()
    except KeyboardInterrupt:
        print("\n\n❌ Operação cancelada pelo usuário")
    except Exception as e:
        print(f"\n\n❌ Erro ao gerar chaves: {e}")
