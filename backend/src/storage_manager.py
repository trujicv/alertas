"""
Gestor de persistencia de datos.
Maneja el almacenamiento de emails y UIDs procesados.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Set, Optional
from datetime import datetime


class StorageManager:
    """Gestor de almacenamiento de datos en JSON."""
    
    def __init__(self):
        """Inicializa el gestor de almacenamiento."""
        self.logger = logging.getLogger(__name__)
        self.data_dir = Path(__file__).parent.parent / "data"
        self.emails_file = self.data_dir / "emails.json"
        self.schedule_file = self.data_dir / "schedule.json"
        
        # Asegurar que el directorio existe
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Inicializar archivos si no existen
        self._init_files()
    
    def _init_files(self) -> None:
        """Inicializa archivos de datos si no existen."""
        if not self.emails_file.exists():
            self._write_json(self.emails_file, {
                "processed_uids": [],
                "emails": []
            })
        
        if not self.schedule_file.exists():
            self._write_json(self.schedule_file, {
                "activities": []
            })
    
    def _read_json(self, file_path: Path) -> Dict[str, Any]:
        """
        Lee un archivo JSON.
        
        Args:
            file_path: Ruta del archivo
            
        Returns:
            Contenido del archivo como diccionario
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            self.logger.error(f"Error al parsear {file_path.name}: {e}")
            return {}
        except Exception as e:
            self.logger.error(f"Error al leer {file_path.name}: {e}")
            return {}
    
    def _write_json(self, file_path: Path, data: Dict[str, Any]) -> bool:
        """
        Escribe datos en un archivo JSON.
        
        Args:
            file_path: Ruta del archivo
            data: Datos a escribir
            
        Returns:
            True si fue exitoso
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            self.logger.error(f"Error al escribir {file_path.name}: {e}")
            return False
    
    # Gestión de emails
    
    def save_email(self, email_data: Dict[str, Any]) -> bool:
        """
        Guarda un nuevo email.
        
        Args:
            email_data: Datos del email a guardar
            
        Returns:
            True si fue exitoso
        """
        try:
            data = self._read_json(self.emails_file)
            
            # Agregar timestamp si no existe
            if 'saved_at' not in email_data:
                email_data['saved_at'] = datetime.now().isoformat()
            
            # Agregar el email
            data['emails'].append(email_data)
            
            # Limitar a los últimos 1000 emails
            if len(data['emails']) > 1000:
                data['emails'] = data['emails'][-1000:]
            
            success = self._write_json(self.emails_file, data)
            if success:
                self.logger.debug(f"Email guardado: {email_data.get('subject', 'Sin asunto')}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error al guardar email: {e}")
            return False
    
    def get_all_emails(self) -> List[Dict[str, Any]]:
        """
        Obtiene todos los emails guardados.
        
        Returns:
            Lista de emails
        """
        data = self._read_json(self.emails_file)
        return data.get('emails', [])
    
    def get_recent_emails(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Obtiene los emails más recientes.
        
        Args:
            limit: Número máximo de emails a retornar
            
        Returns:
            Lista de emails recientes
        """
        emails = self.get_all_emails()
        return emails[-limit:] if emails else []
    
    def clear_emails(self) -> bool:
        """
        Elimina todos los emails guardados.
        
        Returns:
            True si fue exitoso
        """
        data = self._read_json(self.emails_file)
        data['emails'] = []
        return self._write_json(self.emails_file, data)
    
    # Gestión de UIDs procesados
    
    def save_processed_uid(self, uid: str) -> bool:
        """
        Guarda un UID como procesado.
        
        Args:
            uid: UID del email procesado
            
        Returns:
            True si fue exitoso
        """
        try:
            data = self._read_json(self.emails_file)
            
            if uid not in data['processed_uids']:
                data['processed_uids'].append(uid)
                
                # Limitar a los últimos 10000 UIDs
                if len(data['processed_uids']) > 10000:
                    data['processed_uids'] = data['processed_uids'][-10000:]
                
                return self._write_json(self.emails_file, data)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error al guardar UID procesado: {e}")
            return False
    
    def get_processed_uids(self) -> Set[str]:
        """
        Obtiene todos los UIDs procesados.
        
        Returns:
            Set de UIDs procesados
        """
        data = self._read_json(self.emails_file)
        return set(data.get('processed_uids', []))
    
    def clear_processed_uids(self) -> bool:
        """
        Elimina todos los UIDs procesados.
        
        Returns:
            True si fue exitoso
        """
        data = self._read_json(self.emails_file)
        data['processed_uids'] = []
        return self._write_json(self.emails_file, data)
    
    # Gestión de actividades programadas
    
    def save_activity(self, activity: Dict[str, Any]) -> bool:
        """
        Guarda una actividad programada.
        
        Args:
            activity: Datos de la actividad
            
        Returns:
            True si fue exitoso
        """
        try:
            data = self._read_json(self.schedule_file)
            
            # Agregar timestamp si no existe
            if 'created_at' not in activity:
                activity['created_at'] = datetime.now().isoformat()
            
            data['activities'].append(activity)
            
            success = self._write_json(self.schedule_file, data)
            if success:
                self.logger.debug(f"Actividad guardada: {activity.get('title', 'Sin título')}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error al guardar actividad: {e}")
            return False
    
    def get_activities(self) -> List[Dict[str, Any]]:
        """
        Obtiene todas las actividades programadas.
        
        Returns:
            Lista de actividades
        """
        data = self._read_json(self.schedule_file)
        return data.get('activities', [])
    
    def update_activity(self, activity_id: str, updated_data: Dict[str, Any]) -> bool:
        """
        Actualiza una actividad existente.
        
        Args:
            activity_id: ID de la actividad
            updated_data: Datos actualizados
            
        Returns:
            True si fue exitoso
        """
        try:
            data = self._read_json(self.schedule_file)
            activities = data.get('activities', [])
            
            for i, activity in enumerate(activities):
                if activity.get('id') == activity_id:
                    activities[i].update(updated_data)
                    activities[i]['updated_at'] = datetime.now().isoformat()
                    data['activities'] = activities
                    return self._write_json(self.schedule_file, data)
            
            self.logger.warning(f"Actividad no encontrada: {activity_id}")
            return False
            
        except Exception as e:
            self.logger.error(f"Error al actualizar actividad: {e}")
            return False
    
    def delete_activity(self, activity_id: str) -> bool:
        """
        Elimina una actividad.
        
        Args:
            activity_id: ID de la actividad a eliminar
            
        Returns:
            True si fue exitoso
        """
        try:
            data = self._read_json(self.schedule_file)
            activities = data.get('activities', [])
            
            initial_length = len(activities)
            activities = [a for a in activities if a.get('id') != activity_id]
            
            if len(activities) < initial_length:
                data['activities'] = activities
                return self._write_json(self.schedule_file, data)
            
            self.logger.warning(f"Actividad no encontrada: {activity_id}")
            return False
            
        except Exception as e:
            self.logger.error(f"Error al eliminar actividad: {e}")
            return False
    
    def clear_activities(self) -> bool:
        """
        Elimina todas las actividades.
        
        Returns:
            True si fue exitoso
        """
        data = self._read_json(self.schedule_file)
        data['activities'] = []
        return self._write_json(self.schedule_file, data)


# Instancia global
storage = StorageManager()
