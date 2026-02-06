"""
Servicio TOTP (Time-based One-Time Password)
Implementación manual compatible con RFC 6238 y Microsoft Authenticator
Principio: Single Responsibility - Solo maneja generación y validación TOTP
"""
import base64
import hashlib
import hmac
import secrets
import struct
import time
from typing import Tuple
from urllib.parse import quote

from app.config import settings


class TOTPService:
    """
    Servicio para generar y validar códigos TOTP
    Compatible con Microsoft Authenticator (RFC 6238)
    """
    
    def __init__(self):
        self.digits = settings.totp_digits
        self.interval = settings.totp_interval
        self.issuer = settings.totp_issuer
    
    def generate_secret(self) -> str:
        """
        Genera un secret aleatorio en formato base32
        
        Returns:
            Secret en formato base32 (compatible con authenticators)
        """
        # Generar 20 bytes aleatorios (160 bits - recomendado por RFC)
        random_bytes = secrets.token_bytes(20)
        # Convertir a base32 (formato estándar para TOTP)
        secret = base64.b32encode(random_bytes).decode('utf-8')
        return secret
    
    def _get_hotp_token(self, secret: str, counter: int) -> str:
        """
        Genera un código HOTP (HMAC-based One-Time Password)
        Implementación según RFC 4226
        
        Args:
            secret: Secret en formato base32
            counter: Contador (para TOTP es timestamp / interval)
            
        Returns:
            Código de 6 dígitos
        """
        # Decodificar secret de base32
        key = base64.b32decode(secret, casefold=True)
        
        # Convertir counter a bytes (8 bytes, big-endian)
        counter_bytes = struct.pack('>Q', counter)
        
        # Calcular HMAC-SHA1
        hmac_hash = hmac.new(key, counter_bytes, hashlib.sha1).digest()
        
        # Dynamic truncation (RFC 4226 Section 5.3)
        offset = hmac_hash[-1] & 0x0F
        truncated_hash = hmac_hash[offset:offset + 4]
        
        # Convertir a entero de 4 bytes
        code = struct.unpack('>I', truncated_hash)[0]
        
        # Aplicar máscara para obtener 31 bits
        code = code & 0x7FFFFFFF
        
        # Obtener últimos N dígitos
        code = code % (10 ** self.digits)
        
        # Formatear con ceros a la izquierda
        return str(code).zfill(self.digits)
    
    def generate_totp(self, secret: str, timestamp: int = None) -> str:
        """
        Genera un código TOTP para el timestamp actual
        
        Args:
            secret: Secret en formato base32
            timestamp: Timestamp Unix (None para usar actual)
            
        Returns:
            Código TOTP de 6 dígitos
        """
        if timestamp is None:
            timestamp = int(time.time())
        
        # Calcular counter basado en intervalo de tiempo
        counter = timestamp // self.interval
        
        return self._get_hotp_token(secret, counter)
    
    def verify_totp(self, secret: str, token: str, window: int = 1) -> bool:
        """
        Verifica un código TOTP
        
        Args:
            secret: Secret en formato base32
            token: Código a verificar
            window: Ventana de tiempo (permite códigos +/- window intervalos)
                   Por defecto 1 = permite código actual, anterior y siguiente
            
        Returns:
            True si el código es válido
        """
        if not token or len(token) != self.digits:
            return False
        
        current_timestamp = int(time.time())
        current_counter = current_timestamp // self.interval
        
        # Verificar código actual y ventana de tiempo
        for i in range(-window, window + 1):
            counter = current_counter + i
            expected_token = self._get_hotp_token(secret, counter)
            
            if token == expected_token:
                return True
        
        return False
    
    def get_provisioning_uri(self, email: str, secret: str) -> str:
        """
        Genera URI para código QR (formato otpauth://)
        Compatible con Microsoft Authenticator y Google Authenticator
        
        Args:
            email: Email del usuario
            secret: Secret en formato base32
            
        Returns:
            URI en formato otpauth://totp/...
        """
        # Formato: otpauth://totp/Issuer:email?secret=SECRET&issuer=Issuer
        encoded_email = quote(email)
        encoded_issuer = quote(self.issuer)
        
        uri = (
            f"otpauth://totp/{encoded_issuer}:{encoded_email}"
            f"?secret={secret}"
            f"&issuer={encoded_issuer}"
            f"&algorithm=SHA1"
            f"&digits={self.digits}"
            f"&period={self.interval}"
        )
        
        return uri
    
    def format_secret_for_manual_entry(self, secret: str) -> str:
        """
        Formatea el secret para entrada manual (grupos de 4 caracteres)
        
        Args:
            secret: Secret en formato base32
            
        Returns:
            Secret formateado (ej: "JBSW Y3DP EHPK 3PXP")
        """
        # Agrupar en bloques de 4 caracteres
        groups = [secret[i:i+4] for i in range(0, len(secret), 4)]
        return ' '.join(groups)
