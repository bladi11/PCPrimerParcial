from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, Column, Integer, String, Date, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from pydantic import BaseModel
from datetime import date
from typing import List, Optional

# Configuración de la conexión a la base de datos MySQL
SQLALCHEMY_DATABASE_URL = "mysql://root:@localhost/rrhh"
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Declaración de la base de modelos
Base = declarative_base()

# Definición del modelo de datos para empleados
class Empleado(Base):
    __tablename__ = "empleados"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), index=True)
    apellido = Column(String(50), index=True)
    email = Column(String(100), unique=True, index=True)
    fecha_nacimiento = Column(Date)
    puesto = Column(String(100))
    salario = Column(Float)
    proyecto_id = Column(Integer, ForeignKey('proyectos.id'), nullable=True)

    proyecto = relationship("Proyecto", back_populates="empleados")

# Definición del modelo de datos para proyectos
class Proyecto(Base):
    __tablename__ = "proyectos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), index=True)
    descripcion = Column(String(500))
    fecha_inicio = Column(Date)
    fecha_fin = Column(Date)
    porcentaje_completado = Column(Float)

    empleados = relationship("Empleado", back_populates="proyecto")

# Crea todas las tablas en la base de datos
Base.metadata.create_all(bind=engine)

# Crea una sesión de base de datos
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Modelos Pydantic para la entrada y salida de datos

class EmpleadoBase(BaseModel):
    nombre: str
    apellido: str
    email: str
    fecha_nacimiento: date
    puesto: str
    salario: float

class EmpleadoCreate(EmpleadoBase):
    pass

class EmpleadoUpdate(EmpleadoBase):
    proyecto_id: Optional[int] = None

class EmpleadoResponse(EmpleadoBase):
    id: int
    proyecto_id: Optional[int]

    class Config:
        orm_mode = True

class ProyectoBase(BaseModel):
    nombre: str
    descripcion: str
    fecha_inicio: date
    fecha_fin: date
    porcentaje_completado: float

class ProyectoCreate(ProyectoBase):
    pass

class ProyectoUpdate(ProyectoBase):
    pass

class ProyectoResponse(ProyectoBase):
    id: int
    empleados: List[EmpleadoResponse] = []

    class Config:
        orm_mode = True

app = FastAPI()

# Operaciones CRUD para Empleados

@app.post('/empleados/', response_model=EmpleadoResponse)
def create_empleado(empleado: EmpleadoCreate):
    db = SessionLocal()
    db_empleado = Empleado(**empleado.dict())
    db.add(db_empleado)
    db.commit()
    db.refresh(db_empleado)
    return db_empleado

@app.get('/empleados/', response_model=List[EmpleadoResponse])
def get_all_empleados():
    db = SessionLocal()
    return db.query(Empleado).all()

@app.get('/empleados/{empleado_id}', response_model=EmpleadoResponse)
def get_empleado_by_id(empleado_id: int):
    db = SessionLocal()
    empleado = db.query(Empleado).filter(Empleado.id == empleado_id).first()
    if empleado is None:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    return empleado

@app.put('/empleados/{empleado_id}', response_model=EmpleadoResponse)
def update_empleado(empleado_id: int, empleado: EmpleadoUpdate):
    db = SessionLocal()
    db_empleado = db.query(Empleado).filter(Empleado.id == empleado_id).first()
    if db_empleado is None:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    for var, value in empleado.dict().items():
        setattr(db_empleado, var, value)
    db.commit()
    db.refresh(db_empleado)
    return db_empleado

@app.delete('/empleados/{empleado_id}')
def delete_empleado(empleado_id: int):
    db = SessionLocal()
    db_empleado = db.query(Empleado).filter(Empleado.id == empleado_id).first()
    if db_empleado is None:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    db.delete(db_empleado)
    db.commit()
    return {"message": "Empleado eliminado exitosamente"}

# Operaciones CRUD para Proyectos

@app.post('/proyectos/', response_model=ProyectoResponse)
def create_proyecto(proyecto: ProyectoCreate):
    db = SessionLocal()
    db_proyecto = Proyecto(**proyecto.dict())
    db.add(db_proyecto)
    db.commit()
    db.refresh(db_proyecto)
    return db_proyecto

@app.get('/proyectos/', response_model=List[ProyectoResponse])
def get_all_proyectos():
    db = SessionLocal()
    return db.query(Proyecto).all()

@app.get('/proyectos/{proyecto_id}', response_model=ProyectoResponse)
def get_proyecto_by_id(proyecto_id: int):
    db = SessionLocal()
    proyecto = db.query(Proyecto).filter(Proyecto.id == proyecto_id).first()
    if proyecto is None:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return proyecto

@app.put('/proyectos/{proyecto_id}', response_model=ProyectoResponse)
def update_proyecto(proyecto_id: int, proyecto: ProyectoUpdate):
    db = SessionLocal()
    db_proyecto = db.query(Proyecto).filter(Proyecto.id == proyecto_id).first()
    if db_proyecto is None:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    for var, value in proyecto.dict().items():
        setattr(db_proyecto, var, value)
    db.commit()
    db.refresh(db_proyecto)
    return db_proyecto

# Asignar empleado a proyecto
@app.post('/proyectos/{proyecto_id}/asignar/{empleado_id}')
def asignar_empleado_a_proyecto(proyecto_id: int, empleado_id: int):
    db = SessionLocal()
    empleado = db.query(Empleado).filter(Empleado.id == empleado_id).first()
    if empleado is None:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    if empleado.proyecto_id is not None:
        raise HTTPException(status_code=400, detail="El empleado ya está asignado a un proyecto")
    
    proyecto = db.query(Proyecto).filter(Proyecto.id == proyecto_id).first()
    if proyecto is None:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    empleado.proyecto_id = proyecto_id
    db.commit()
    return {"message": "Empleado asignado al proyecto exitosamente"}

# Iniciar el programa (uvicorn main:app --reload)