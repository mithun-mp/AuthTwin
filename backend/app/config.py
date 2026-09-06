import os
import socket
from typing import Set, Tuple
from pydantic_settings import BaseSettings

from pydantic import model_validator

class Settings(BaseSettings):
    PROJECT_NAME: str = "AuthTwin"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./authtwin.db")
    ALLOWED_ORIGINS: list[str] = ["*"]
    
    AUTHTWIN_API_HOST: str = os.getenv("AUTHTWIN_API_HOST", "127.0.0.1")
    AUTHTWIN_API_PORT: int = int(os.getenv("AUTHTWIN_API_PORT", "5000"))
    AUTHTWIN_FRONTEND_PORT: int = int(os.getenv("AUTHTWIN_FRONTEND_PORT", "5173"))
    AUTHTWIN_DEMO_MODE: bool = os.getenv("AUTHTWIN_DEMO_MODE", "false").lower() == "true"
    
    # Interceptor limits and security constants
    MAX_BODY_BYTES: int = 10 * 1024 * 1024  # 10 MB limit
    MAX_BUFFER_TXS: int = 1000              # Max live transactions per buffer session
    PROXY_PREFIX: str = "/api/v1/interceptor/proxy"
    
    class Config:
        case_sensitive = True

    @model_validator(mode="after")
    def validate_infrastructure_ports(self) -> "Settings":
        if self.AUTHTWIN_API_PORT < 5000 or self.AUTHTWIN_API_PORT > 5999:
            raise ValueError(f"AuthTwin API port ({self.AUTHTWIN_API_PORT}) must be between 5000 and 5999.")
        if self.AUTHTWIN_FRONTEND_PORT < 5000 or self.AUTHTWIN_FRONTEND_PORT > 5999:
            raise ValueError(f"AuthTwin Frontend port ({self.AUTHTWIN_FRONTEND_PORT}) must be between 5000 and 5999.")
        if self.AUTHTWIN_API_PORT == self.AUTHTWIN_FRONTEND_PORT:
            raise ValueError(f"AuthTwin API port ({self.AUTHTWIN_API_PORT}) and Frontend port ({self.AUTHTWIN_FRONTEND_PORT}) cannot be the same.")
        return self

    def get_control_plane_endpoints(self) -> Set[Tuple[str, int]]:

        """
        Returns normalized host/IP and port tuples that represent AuthTwin's
        control-plane services (FastAPI API server and Vite Frontend UI).
        """
        endpoints = set()
        ports = {self.AUTHTWIN_API_PORT, self.AUTHTWIN_FRONTEND_PORT}
        base_hosts = {"127.0.0.1", "localhost", "0.0.0.0", self.AUTHTWIN_API_HOST.lower()}
        
        # Try resolving hostnames to IP addresses
        resolved_ips = set()
        for host in list(base_hosts):
            try:
                ip = socket.gethostbyname(host)
                resolved_ips.add(ip)
            except Exception:
                pass
        
        all_hosts = base_hosts.union(resolved_ips)
        for h in all_hosts:
            for p in ports:
                endpoints.add((h.lower(), p))
        return endpoints

settings = Settings()

