"""
Data Encryption

This module provides secure data encryption and decryption capabilities
with support for multiple encryption algorithms and key management.
"""

import logging
import base64
import hashlib
import secrets
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass
from enum import Enum
import json
from datetime import datetime

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    from cryptography.hazmat.backends import default_backend
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False
    logging.warning("cryptography not available. Install with: pip install cryptography")

logger = logging.getLogger(__name__)

class EncryptionAlgorithm(Enum):
    """Supported encryption algorithms."""
    AES_256_GCM = "aes_256_gcm"
    AES_256_CBC = "aes_256_cbc"
    RSA_2048 = "rsa_2048"
    RSA_4096 = "rsa_4096"
    FERNET = "fernet"

@dataclass
class EncryptionConfig:
    """Configuration for encryption."""
    algorithm: EncryptionAlgorithm = EncryptionAlgorithm.FERNET
    key_size: int = 32
    salt_size: int = 16
    iterations: int = 100000
    use_compression: bool = True
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class EncryptedData:
    """Encrypted data container."""
    encrypted_data: bytes
    algorithm: str
    key_id: Optional[str] = None
    salt: Optional[bytes] = None
    iv: Optional[bytes] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: str = None
    version: str = "1.0"
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

class DataEncryption:
    """Data encryption and decryption manager."""
    
    def __init__(
        self,
        config: Optional[EncryptionConfig] = None,
        key_storage: Optional[Dict[str, bytes]] = None
    ):
        """Initialize data encryption.
        
        Args:
            config: Encryption configuration
            key_storage: Optional key storage for key management
        """
        if not CRYPTOGRAPHY_AVAILABLE:
            raise ImportError(
                "cryptography library not available. Install with: pip install cryptography"
            )
        
        self.config = config or EncryptionConfig()
        self.key_storage = key_storage or {}
        self.active_keys: Dict[str, bytes] = {}
        
        logger.info(f"Data encryption initialized with {self.config.algorithm.value}")
    
    def generate_key(self, key_id: Optional[str] = None) -> str:
        """Generate a new encryption key.
        
        Args:
            key_id: Optional key identifier
            
        Returns:
            Key identifier
        """
        if key_id is None:
            key_id = secrets.token_urlsafe(16)
        
        if self.config.algorithm == EncryptionAlgorithm.FERNET:
            key = Fernet.generate_key()
        elif self.config.algorithm in [EncryptionAlgorithm.AES_256_GCM, EncryptionAlgorithm.AES_256_CBC]:
            key = secrets.token_bytes(self.config.key_size)
        elif self.config.algorithm in [EncryptionAlgorithm.RSA_2048, EncryptionAlgorithm.RSA_4096]:
            key_size = 2048 if self.config.algorithm == EncryptionAlgorithm.RSA_2048 else 4096
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=key_size,
                backend=default_backend()
            )
            key = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
        else:
            raise ValueError(f"Unsupported algorithm: {self.config.algorithm}")
        
        self.active_keys[key_id] = key
        self.key_storage[key_id] = key
        
        logger.info(f"Generated key: {key_id}")
        return key_id
    
    def derive_key_from_password(
        self,
        password: str,
        salt: Optional[bytes] = None,
        key_id: Optional[str] = None
    ) -> str:
        """Derive encryption key from password.
        
        Args:
            password: Password to derive key from
            salt: Optional salt (generated if not provided)
            key_id: Optional key identifier
            
        Returns:
            Key identifier
        """
        if key_id is None:
            key_id = secrets.token_urlsafe(16)
        
        if salt is None:
            salt = secrets.token_bytes(self.config.salt_size)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=self.config.key_size,
            salt=salt,
            iterations=self.config.iterations,
            backend=default_backend()
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        
        self.active_keys[key_id] = key
        self.key_storage[key_id] = key
        
        logger.info(f"Derived key from password: {key_id}")
        return key_id
    
    def encrypt_data(
        self,
        data: Union[str, bytes, Dict[str, Any]],
        key_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> EncryptedData:
        """Encrypt data.
        
        Args:
            data: Data to encrypt
            key_id: Key identifier (generates new key if not provided)
            metadata: Optional metadata
            
        Returns:
            EncryptedData object
        """
        # Generate key if not provided
        if key_id is None:
            key_id = self.generate_key()
        
        if key_id not in self.active_keys:
            raise ValueError(f"Key not found: {key_id}")
        
        key = self.active_keys[key_id]
        
        # Convert data to bytes
        if isinstance(data, str):
            data_bytes = data.encode('utf-8')
        elif isinstance(data, dict):
            data_bytes = json.dumps(data).encode('utf-8')
        elif isinstance(data, bytes):
            data_bytes = data
        else:
            raise ValueError(f"Unsupported data type: {type(data)}")
        
        # Apply compression if enabled
        if self.config.use_compression:
            import gzip
            data_bytes = gzip.compress(data_bytes)
        
        # Encrypt data based on algorithm
        if self.config.algorithm == EncryptionAlgorithm.FERNET:
            fernet = Fernet(key)
            encrypted_data = fernet.encrypt(data_bytes)
            salt = None
            iv = None
        elif self.config.algorithm in [EncryptionAlgorithm.AES_256_GCM, EncryptionAlgorithm.AES_256_CBC]:
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            from cryptography.hazmat.backends import default_backend
            
            # Generate IV
            iv = secrets.token_bytes(16)
            
            if self.config.algorithm == EncryptionAlgorithm.AES_256_GCM:
                cipher = Cipher(
                    algorithms.AES(key),
                    modes.GCM(iv),
                    backend=default_backend()
                )
            else:  # AES_256_CBC
                cipher = Cipher(
                    algorithms.AES(key),
                    modes.CBC(iv),
                    backend=default_backend()
                )
            
            encryptor = cipher.encryptor()
            
            # Pad data for CBC mode
            if self.config.algorithm == EncryptionAlgorithm.AES_256_CBC:
                from cryptography.hazmat.primitives import padding
                padder = padding.PKCS7(128).padder()
                data_bytes = padder.update(data_bytes)
                data_bytes += padder.finalize()
            
            encrypted_data = encryptor.update(data_bytes) + encryptor.finalize()
            salt = None
        elif self.config.algorithm in [EncryptionAlgorithm.RSA_2048, EncryptionAlgorithm.RSA_4096]:
            # Load private key to get public key
            private_key = serialization.load_pem_private_key(
                key,
                password=None,
                backend=default_backend()
            )
            public_key = private_key.public_key()
            
            # Encrypt with RSA
            encrypted_data = public_key.encrypt(
                data_bytes,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            salt = None
            iv = None
        else:
            raise ValueError(f"Unsupported algorithm: {self.config.algorithm}")
        
        # Create encrypted data object
        encrypted_obj = EncryptedData(
            encrypted_data=encrypted_data,
            algorithm=self.config.algorithm.value,
            key_id=key_id,
            salt=salt,
            iv=iv,
            metadata=metadata or {}
        )
        
        logger.info(f"Encrypted data with key: {key_id}")
        return encrypted_obj
    
    def decrypt_data(
        self,
        encrypted_data: EncryptedData,
        key_id: Optional[str] = None
    ) -> Union[str, bytes, Dict[str, Any]]:
        """Decrypt data.
        
        Args:
            encrypted_data: EncryptedData object
            key_id: Key identifier (uses encrypted_data.key_id if not provided)
            
        Returns:
            Decrypted data
        """
        # Use key_id from encrypted data if not provided
        if key_id is None:
            key_id = encrypted_data.key_id
        
        if key_id is None:
            raise ValueError("Key ID not provided")
        
        if key_id not in self.active_keys:
            raise ValueError(f"Key not found: {key_id}")
        
        key = self.active_keys[key_id]
        
        # Decrypt data based on algorithm
        if encrypted_data.algorithm == EncryptionAlgorithm.FERNET.value:
            fernet = Fernet(key)
            decrypted_data = fernet.decrypt(encrypted_data.encrypted_data)
        elif encrypted_data.algorithm in [EncryptionAlgorithm.AES_256_GCM.value, EncryptionAlgorithm.AES_256_CBC.value]:
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            from cryptography.hazmat.backends import default_backend
            
            if encrypted_data.iv is None:
                raise ValueError("IV not found for AES decryption")
            
            if encrypted_data.algorithm == EncryptionAlgorithm.AES_256_GCM.value:
                cipher = Cipher(
                    algorithms.AES(key),
                    modes.GCM(encrypted_data.iv),
                    backend=default_backend()
                )
            else:  # AES_256_CBC
                cipher = Cipher(
                    algorithms.AES(key),
                    modes.CBC(encrypted_data.iv),
                    backend=default_backend()
                )
            
            decryptor = cipher.decryptor()
            decrypted_data = decryptor.update(encrypted_data.encrypted_data) + decryptor.finalize()
            
            # Unpad data for CBC mode
            if encrypted_data.algorithm == EncryptionAlgorithm.AES_256_CBC.value:
                from cryptography.hazmat.primitives import padding
                unpadder = padding.PKCS7(128).unpadder()
                decrypted_data = unpadder.update(decrypted_data)
                decrypted_data += unpadder.finalize()
        elif encrypted_data.algorithm in [EncryptionAlgorithm.RSA_2048.value, EncryptionAlgorithm.RSA_4096.value]:
            # Load private key
            private_key = serialization.load_pem_private_key(
                key,
                password=None,
                backend=default_backend()
            )
            
            # Decrypt with RSA
            decrypted_data = private_key.decrypt(
                encrypted_data.encrypted_data,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
        else:
            raise ValueError(f"Unsupported algorithm: {encrypted_data.algorithm}")
        
        # Decompress if compression was used
        if self.config.use_compression:
            import gzip
            decrypted_data = gzip.decompress(decrypted_data)
        
        # Try to decode as JSON first, then as string
        try:
            return json.loads(decrypted_data.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            try:
                return decrypted_data.decode('utf-8')
            except UnicodeDecodeError:
                return decrypted_data
    
    def encrypt_file(
        self,
        file_path: str,
        output_path: Optional[str] = None,
        key_id: Optional[str] = None
    ) -> EncryptedData:
        """Encrypt a file.
        
        Args:
            file_path: Path to file to encrypt
            output_path: Optional output path for encrypted file
            key_id: Key identifier
            
        Returns:
            EncryptedData object
        """
        with open(file_path, 'rb') as f:
            data = f.read()
        
        encrypted_data = self.encrypt_data(data, key_id)
        
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(encrypted_data.encrypted_data)
        
        return encrypted_data
    
    def decrypt_file(
        self,
        encrypted_data: EncryptedData,
        output_path: str,
        key_id: Optional[str] = None
    ) -> bytes:
        """Decrypt a file.
        
        Args:
            encrypted_data: EncryptedData object
            output_path: Path to save decrypted file
            key_id: Key identifier
            
        Returns:
            Decrypted data bytes
        """
        # Use key_id from encrypted data if not provided
        if key_id is None:
            key_id = encrypted_data.key_id
        
        if key_id is None:
            raise ValueError("Key ID not provided")
        
        if key_id not in self.active_keys:
            raise ValueError(f"Key not found: {key_id}")
        
        key = self.active_keys[key_id]
        
        # Decrypt data based on algorithm (same logic as decrypt_data but return bytes)
        if encrypted_data.algorithm == EncryptionAlgorithm.FERNET.value:
            fernet = Fernet(key)
            decrypted_data = fernet.decrypt(encrypted_data.encrypted_data)
        elif encrypted_data.algorithm in [EncryptionAlgorithm.AES_256_GCM.value, EncryptionAlgorithm.AES_256_CBC.value]:
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            from cryptography.hazmat.backends import default_backend
            
            if encrypted_data.iv is None:
                raise ValueError("IV not found for AES decryption")
            
            if encrypted_data.algorithm == EncryptionAlgorithm.AES_256_GCM.value:
                cipher = Cipher(
                    algorithms.AES(key),
                    modes.GCM(encrypted_data.iv),
                    backend=default_backend()
                )
            else:  # AES_256_CBC
                cipher = Cipher(
                    algorithms.AES(key),
                    modes.CBC(encrypted_data.iv),
                    backend=default_backend()
                )
            
            decryptor = cipher.decryptor()
            decrypted_data = decryptor.update(encrypted_data.encrypted_data) + decryptor.finalize()
            
            # Unpad data for CBC mode
            if encrypted_data.algorithm == EncryptionAlgorithm.AES_256_CBC.value:
                from cryptography.hazmat.primitives import padding
                unpadder = padding.PKCS7(128).unpadder()
                decrypted_data = unpadder.update(decrypted_data)
                decrypted_data += unpadder.finalize()
        elif encrypted_data.algorithm in [EncryptionAlgorithm.RSA_2048.value, EncryptionAlgorithm.RSA_4096.value]:
            # Load private key
            private_key = serialization.load_pem_private_key(
                key,
                password=None,
                backend=default_backend()
            )
            
            # Decrypt with RSA
            decrypted_data = private_key.decrypt(
                encrypted_data.encrypted_data,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
        else:
            raise ValueError(f"Unsupported algorithm: {encrypted_data.algorithm}")
        
        # Decompress if compression was used
        if self.config.use_compression:
            import gzip
            decrypted_data = gzip.decompress(decrypted_data)
        
        # Write to file
        with open(output_path, 'wb') as f:
            f.write(decrypted_data)
        
        return decrypted_data
    
    def rotate_key(self, old_key_id: str, new_key_id: Optional[str] = None) -> str:
        """Rotate encryption key.
        
        Args:
            old_key_id: Old key identifier
            new_key_id: New key identifier (generates if not provided)
            
        Returns:
            New key identifier
        """
        if new_key_id is None:
            new_key_id = self.generate_key()
        
        if old_key_id not in self.active_keys:
            raise ValueError(f"Old key not found: {old_key_id}")
        
        # Keep old key for decryption, add new key for encryption
        logger.info(f"Key rotated: {old_key_id} -> {new_key_id}")
        return new_key_id
    
    def get_encryption_stats(self) -> Dict[str, Any]:
        """Get encryption statistics."""
        return {
            "algorithm": self.config.algorithm.value,
            "key_size": self.config.key_size,
            "active_keys": len(self.active_keys),
            "total_keys": len(self.key_storage),
            "compression_enabled": self.config.use_compression,
            "iterations": self.config.iterations
        }

# Convenience functions
def create_encryption_manager(**kwargs) -> DataEncryption:
    """Create a data encryption manager."""
    return DataEncryption(**kwargs)

def encrypt_text(
    text: str,
    password: Optional[str] = None,
    algorithm: EncryptionAlgorithm = EncryptionAlgorithm.FERNET
) -> EncryptedData:
    """Convenience function to encrypt text."""
    config = EncryptionConfig(algorithm=algorithm)
    manager = DataEncryption(config)
    
    if password:
        key_id = manager.derive_key_from_password(password)
    else:
        key_id = manager.generate_key()
    
    return manager.encrypt_data(text, key_id)

def decrypt_text(
    encrypted_data: EncryptedData,
    password: Optional[str] = None
) -> str:
    """Convenience function to decrypt text."""
    config = EncryptionConfig(algorithm=EncryptionAlgorithm(encrypted_data.algorithm))
    manager = DataEncryption(config)
    
    if password:
        key_id = manager.derive_key_from_password(password)
    else:
        key_id = encrypted_data.key_id
    
    return manager.decrypt_data(encrypted_data, key_id)
