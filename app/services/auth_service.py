"""
Serviço de Autenticação e Gerenciamento de Usuários
Implementa autenticação segura com bcrypt e controle de tentativas
"""
from flask_bcrypt import Bcrypt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import datetime, timedelta
from typing import Optional, Tuple
import os
import json

from app.models import db, Usuario, AuditLog, horario_brasilia

bcrypt = Bcrypt()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)


class AuthService:
    """Serviço centralizado para autenticação e gerenciamento de usuários"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Gera hash bcrypt de uma senha.
        
        Args:
            password: Senha em texto plano
            
        Returns:
            Hash bcrypt da senha
        """
        return bcrypt.generate_password_hash(password).decode('utf-8')
    
    @staticmethod
    def check_password(password_hash: str, password: str) -> bool:
        """
        Verifica se uma senha corresponde ao hash.
        
        Args:
            password_hash: Hash bcrypt armazenado
            password: Senha em texto plano para verificar
            
        Returns:
            True se a senha é válida, False caso contrário
        """
        return bcrypt.check_password_hash(password_hash, password)
    
    @staticmethod
    def criar_usuario_admin_inicial():
        """
        Cria o usuário admin inicial se não existir nenhum usuário no sistema.
        Usado na primeira inicialização do sistema.
        """
        # Verifica se já existe algum usuário
        if Usuario.query.count() > 0:
            return None
        
        # Obtém credenciais das variáveis de ambiente
        admin_user = os.environ.get('ADMIN_USER', 'admin')
        admin_password = os.environ.get('ADMIN_PASSWORD')
        
        if not admin_password:
            raise ValueError(
                "❌ ERRO: ADMIN_PASSWORD não definida! "
                "Defina a variável de ambiente ADMIN_PASSWORD para criar o usuário inicial."
            )
        
        # Cria usuário admin
        admin = Usuario(
            username=admin_user,
            password_hash=AuthService.hash_password(admin_password),
            nome_completo='Administrador do Sistema',
            ativo=True,
            is_admin=True
        )
        
        db.session.add(admin)
        db.session.commit()
        
        # Log de auditoria
        AuthService.registrar_auditoria(
            usuario=admin_user,
            acao='criar_usuario_admin',
            detalhes={'mensagem': 'Usuário administrador inicial criado'},
            ip_origem='sistema'
        )
        
        return admin
    
    @staticmethod
    def autenticar(username: str, password: str, ip_origem: str) -> Tuple[bool, Optional[Usuario], Optional[str]]:
        """
        Autentica um usuário.
        
        Args:
            username: Nome de usuário
            password: Senha
            ip_origem: IP de origem da tentativa
            
        Returns:
            Tupla (sucesso, usuario, mensagem_erro)
        """
        usuario = Usuario.query.filter_by(username=username).first()
        
        # Usuário não existe
        if not usuario:
            # Log de tentativa falhada
            AuthService.registrar_auditoria(
                usuario=username,
                acao='login_falha',
                detalhes={'motivo': 'usuario_nao_existe'},
                ip_origem=ip_origem
            )
            return False, None, "Usuário ou senha incorretos"
        
        # Verifica se está bloqueado temporariamente
        if usuario.bloqueado_ate and usuario.bloqueado_ate > horario_brasilia():
            tempo_restante = (usuario.bloqueado_ate - horario_brasilia()).seconds // 60
            return False, None, f"Conta bloqueada temporariamente. Tente novamente em {tempo_restante} minutos."
        
        # Verifica se está ativo
        if not usuario.ativo:
            AuthService.registrar_auditoria(
                usuario=username,
                acao='login_falha',
                detalhes={'motivo': 'usuario_inativo'},
                ip_origem=ip_origem
            )
            return False, None, "Conta inativa. Contate o administrador."
        
        # Verifica senha
        if not AuthService.check_password(usuario.password_hash, password):
            # Incrementa tentativas falhas
            usuario.tentativas_login += 1
            
            # Bloqueia após 5 tentativas
            max_tentativas = int(os.environ.get('MAX_LOGIN_ATTEMPTS', 5))
            if usuario.tentativas_login >= max_tentativas:
                tempo_bloqueio = int(os.environ.get('LOGIN_BLOCK_TIME', 15))
                usuario.bloqueado_ate = horario_brasilia() + timedelta(minutes=tempo_bloqueio)
                db.session.commit()
                
                AuthService.registrar_auditoria(
                    usuario=username,
                    acao='conta_bloqueada',
                    detalhes={'tentativas': usuario.tentativas_login, 'tempo_bloqueio_minutos': tempo_bloqueio},
                    ip_origem=ip_origem
                )
                
                return False, None, f"Muitas tentativas falhas. Conta bloqueada por {tempo_bloqueio} minutos."
            
            db.session.commit()
            
            AuthService.registrar_auditoria(
                usuario=username,
                acao='login_falha',
                detalhes={'motivo': 'senha_incorreta', 'tentativas': usuario.tentativas_login},
                ip_origem=ip_origem
            )
            
            return False, None, "Usuário ou senha incorretos"
        
        # Autenticação bem-sucedida
        usuario.tentativas_login = 0
        usuario.bloqueado_ate = None
        usuario.ultimo_login = horario_brasilia()
        db.session.commit()
        
        AuthService.registrar_auditoria(
            usuario=username,
            acao='login_sucesso',
            detalhes={'timestamp': horario_brasilia().isoformat()},
            ip_origem=ip_origem
        )
        
        return True, usuario, None
    
    @staticmethod
    def alterar_senha(usuario: Usuario, senha_atual: str, senha_nova: str) -> Tuple[bool, str]:
        """
        Altera a senha de um usuário.
        
        Args:
            usuario: Objeto Usuario
            senha_atual: Senha atual para verificação
            senha_nova: Nova senha
            
        Returns:
            Tupla (sucesso, mensagem)
        """
        # Verifica senha atual
        if not AuthService.check_password(usuario.password_hash, senha_atual):
            return False, "Senha atual incorreta"
        
        # Valida nova senha
        if len(senha_nova) < 8:
            return False, "A nova senha deve ter no mínimo 8 caracteres"
        
        # Atualiza senha
        usuario.password_hash = AuthService.hash_password(senha_nova)
        db.session.commit()
        
        AuthService.registrar_auditoria(
            usuario=usuario.username,
            acao='alterar_senha',
            detalhes={'timestamp': horario_brasilia().isoformat()},
            ip_origem='sistema'
        )
        
        return True, "Senha alterada com sucesso"
    
    @staticmethod
    def registrar_auditoria(usuario: str, acao: str, detalhes: dict, ip_origem: str):
        """
        Registra uma ação no log de auditoria.
        
        Args:
            usuario: Username do usuário
            acao: Tipo de ação executada
            detalhes: Dicionário com detalhes da ação
            ip_origem: IP de origem
        """
        try:
            log = AuditLog(
                usuario=usuario,
                acao=acao,
                detalhes=json.dumps(detalhes, ensure_ascii=False)
            )
            log.set_ip_origem(ip_origem)
            
            db.session.add(log)
            db.session.commit()
        except Exception as e:
            # Não deixa falha no log de auditoria quebrar a aplicação
            print(f"⚠️ Erro ao registrar auditoria: {e}")
    
    @staticmethod
    def obter_logs_auditoria(usuario: Optional[str] = None, acao: Optional[str] = None, 
                            limite: int = 100) -> list:
        """
        Obtém logs de auditoria com filtros opcionais.
        
        Args:
            usuario: Filtrar por usuário (opcional)
            acao: Filtrar por ação (opcional)
            limite: Número máximo de registros
            
        Returns:
            Lista de logs de auditoria
        """
        query = AuditLog.query
        
        if usuario:
            query = query.filter_by(usuario=usuario)
        if acao:
            query = query.filter_by(acao=acao)
        
        return query.order_by(AuditLog.timestamp.desc()).limit(limite).all()
