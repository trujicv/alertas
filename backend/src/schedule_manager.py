"""
Gestor de actividades programadas.
Permite agregar y eliminar actividades del schedule.json.
"""

import logging
from typing import Dict, Any, List
from datetime import datetime
import uuid

from storage_manager import storage


class ScheduleManager:
    """Gestor de actividades programadas."""
    
    def __init__(self):
        """Inicializa el gestor de actividades."""
        self.logger = logging.getLogger(__name__)
        self.logger.info("Gestor de actividades inicializado")
    
    def add_activity(self, title: str, description: str, 
                    scheduled_date: str) -> Dict[str, Any]:
        """
        Agrega una nueva actividad programada.
        
        Args:
            title: Título de la actividad
            description: Descripción de la actividad
            scheduled_date: Fecha agendada (formato ISO: YYYY-MM-DDTHH:MM:SS)
            
        Returns:
            Diccionario con los datos de la actividad creada
        """
        try:
            # Validar fecha agendada
            try:
                datetime.fromisoformat(scheduled_date)
            except ValueError:
                raise ValueError(f"Formato de fecha inválido: {scheduled_date}. Use formato ISO.")
            
            # Crear actividad
            activity = {
                'id': str(uuid.uuid4()),
                'title': title,
                'description': description,
                'created_at': datetime.now().isoformat(),
                'scheduled_date': scheduled_date
            }
            
            # Guardar en storage
            if storage.save_activity(activity):
                self.logger.info(f"Actividad agregada: '{title}' para {scheduled_date}")
                return activity
            else:
                raise RuntimeError("Error al guardar la actividad")
            
        except Exception as e:
            self.logger.error(f"Error al agregar actividad: {e}")
            raise
    
    def remove_activity(self, activity_id: str) -> bool:
        """
        Elimina una actividad.
        
        Args:
            activity_id: ID de la actividad a eliminar
            
        Returns:
            True si fue exitoso
        """
        try:
            success = storage.delete_activity(activity_id)
            
            if success:
                self.logger.info(f"Actividad eliminada: {activity_id}")
            else:
                self.logger.warning(f"No se pudo eliminar actividad: {activity_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error al eliminar actividad: {e}")
            return False
    
    def get_all_activities(self) -> List[Dict[str, Any]]:
        """
        Obtiene todas las actividades.
        
        Returns:
            Lista de actividades
        """
        activities = storage.get_activities()
        self.logger.debug(f"Obtenidas {len(activities)} actividades")
        return activities


# Instancia global
scheduler = ScheduleManager()
