from sqlalchemy import DDL, event
from main import db

# Trigger 1: conductor_bonus
trigger_1 = DDL("""
CREATE TRIGGER conductor_bonus
AFTER INSERT ON conductor
FOR EACH ROW
BEGIN
    UPDATE worker w
    JOIN professor p ON w.id = p.worker_id
    SET w.salary = w.salary * 1.15
    WHERE p.id = NEW.professor_id;
END;
""")

# Trigger 2: gerencia_alocacao_instrumento
trigger_2 = DDL("""
CREATE TRIGGER gerencia_alocacao_instrumento
BEFORE UPDATE ON instrument
FOR EACH ROW
BEGIN
    IF NEW.status = 'EM_MANUTENCAO' AND OLD.status <> 'EM_MANUTENCAO' THEN
        SET NEW.dependency_id = NULL;
    END IF;
    
    IF NEW.dependency_id IS NOT NULL AND NEW.status <> 'APTO' THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'Instrumento deve estar APTO para ser alocado';
    END IF;
END;
""")

# Attach triggers to relevant tables AFTER they are created:

# For conductor_bonus, attach to the conductor table
event.listen(db.metadata.tables['conductor'], 'after_create', trigger_1)

# For gerencia_alocacao_instrumento, attach to the instrument table
event.listen(db.metadata.tables['instrument'], 'after_create', trigger_2)
