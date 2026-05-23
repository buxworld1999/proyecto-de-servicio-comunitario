-- =============================================================================
-- migrations/schema.sql
-- Esquema unificado de la base de datos SIGME
-- Sustituye los CREATE TABLE IF NOT EXISTS dispersos en el código Python.
-- Ejecutar una sola vez sobre la base de datos destino.
-- =============================================================================

-- Habilitar extensión para UUIDs (opcional)
-- CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- -----------------------------------------------------------------------------
-- 1. ANO_ESCOLAR
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ano_escolar (
    codigo      VARCHAR(20)  PRIMARY KEY,
    descripcion VARCHAR(100) NOT NULL,
    ano_inicio  INTEGER,
    ano_fin     INTEGER,
    fecha_inicio DATE         NOT NULL,
    fecha_fin    DATE         NOT NULL,
    activo      BOOLEAN      DEFAULT TRUE,
    estado      CHAR(1)      DEFAULT 'A'  -- 'A'=Activo, 'I'=Inactivo
);

-- -----------------------------------------------------------------------------
-- 2. GRADO
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS grado (
    codigo      VARCHAR(20)  PRIMARY KEY,
    nombre      VARCHAR(100) NOT NULL,
    numero_ano  INTEGER      UNIQUE NOT NULL,
    activo      BOOLEAN      DEFAULT TRUE
);

-- Datos base de grados (1ro a 6to)
INSERT INTO grado (codigo, nombre, numero_ano) VALUES
    ('1', 'Primer Año',   1),
    ('2', 'Segundo Año',  2),
    ('3', 'Tercer Año',   3),
    ('4', 'Cuarto Año',   4),
    ('5', 'Quinto Año',   5),
    ('6', 'Sexto Año',    6)
ON CONFLICT (codigo) DO NOTHING;

-- -----------------------------------------------------------------------------
-- 3. PERSONAL
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS personal (
    cedula         VARCHAR(20)  PRIMARY KEY,
    nombres        VARCHAR(100) NOT NULL,
    apellidos      VARCHAR(100) NOT NULL,
    cargo          VARCHAR(50)  NOT NULL,
    especialidad   VARCHAR(100),
    telefono       VARCHAR(20),
    correo         VARCHAR(100),
    fecha_nacimiento DATE,
    genero         CHAR(1),
    fecha_ingreso  DATE,
    turno          CHAR(1),
    carga_horaria  INTEGER,
    estado         CHAR(1)      DEFAULT 'A',
    observaciones  TEXT
);

-- -----------------------------------------------------------------------------
-- 4. SECCION
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS seccion (
    codigo               VARCHAR(20)  PRIMARY KEY,
    letra                CHAR(1)      NOT NULL,
    codigo_grado         VARCHAR(20)  NOT NULL REFERENCES grado(codigo),
    turno                CHAR(1)      NOT NULL,   -- 'M'=Mañana, 'T'=Tarde
    cedula_docente_guia  VARCHAR(20)  REFERENCES personal(cedula),
    aula_asignada        VARCHAR(20),
    capacidad_maxima     INTEGER      DEFAULT 30,
    total_estudiantes    INTEGER      DEFAULT 0,
    estudiantes_varones  INTEGER      DEFAULT 0,
    estudiantes_hembras  INTEGER      DEFAULT 0,
    codigo_ano_escolar   VARCHAR(20)  NOT NULL REFERENCES ano_escolar(codigo),
    activo               BOOLEAN      DEFAULT TRUE
);

-- -----------------------------------------------------------------------------
-- 5. MATERIA
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS materia (
    codigo          VARCHAR(20)  PRIMARY KEY,
    nombre          VARCHAR(100) NOT NULL,
    horas_semanales INTEGER      NOT NULL DEFAULT 5,
    codigo_grado    VARCHAR(20)  NOT NULL REFERENCES grado(codigo),
    area_formacion  VARCHAR(100),
    estado          CHAR(1)      DEFAULT 'A'
);

-- -----------------------------------------------------------------------------
-- 6. ESTUDIANTE
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS estudiante (
    cedula          VARCHAR(20)  PRIMARY KEY,
    nacionalidad    CHAR(1)      DEFAULT 'V',
    nombres         VARCHAR(100) NOT NULL,
    apellidos       VARCHAR(100) NOT NULL,
    fecha_nacimiento DATE,
    genero          CHAR(1),
    telefono        VARCHAR(20),
    correo          VARCHAR(100),
    direccion       TEXT,
    estado          CHAR(1)      DEFAULT 'A',
    foto            BYTEA
);

-- -----------------------------------------------------------------------------
-- 7. REPRESENTANTE
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS representante (
    cedula      VARCHAR(20)  PRIMARY KEY,
    nombres     VARCHAR(100) NOT NULL,
    apellidos   VARCHAR(100) NOT NULL,
    parentesco  VARCHAR(50),
    telefono    VARCHAR(20),
    correo      VARCHAR(100),
    ocupacion   VARCHAR(100),
    foto        BYTEA
);

-- -----------------------------------------------------------------------------
-- 8. MATRICULA
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS matricula (
    id                  SERIAL       PRIMARY KEY,
    cedula_estudiante   VARCHAR(20)  NOT NULL REFERENCES estudiante(cedula),
    codigo_ano_escolar  VARCHAR(20)  NOT NULL REFERENCES ano_escolar(codigo),
    codigo_seccion      VARCHAR(20)  NOT NULL REFERENCES seccion(codigo),
    cedula_representante VARCHAR(20) REFERENCES representante(cedula),
    fecha_matricula     DATE         NOT NULL DEFAULT CURRENT_DATE,
    numero_lista        INTEGER,
    condicion_ingreso   CHAR(1),   -- 'N'=Nuevo, 'R'=Repitiente, 'T'=Trasladado, 'P'=Promovido
    procedencia         VARCHAR(200),
    ano_que_cursa       INTEGER,
    ano_inicio_cursante INTEGER,
    estado_matricula    CHAR(1)      DEFAULT 'A',
    observaciones       TEXT,
    fecha_retiro        DATE,
    motivo_retiro       VARCHAR(200),
    foto_estudiante     BYTEA,
    foto_representante  BYTEA,
    UNIQUE (cedula_estudiante, codigo_ano_escolar)
);

-- -----------------------------------------------------------------------------
-- 9. ASIGNACION_DOCENTE
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS asignacion_docente (
    id                  SERIAL       PRIMARY KEY,
    cedula_docente      VARCHAR(20)  NOT NULL REFERENCES personal(cedula),
    codigo_materia      VARCHAR(20)  NOT NULL REFERENCES materia(codigo),
    codigo_seccion      VARCHAR(20)  NOT NULL REFERENCES seccion(codigo),
    codigo_ano_escolar  VARCHAR(20)  NOT NULL REFERENCES ano_escolar(codigo),
    horas_asignadas     INTEGER,
    turno               CHAR(1)      DEFAULT 'M',
    UNIQUE (codigo_materia, codigo_seccion, codigo_ano_escolar)
);

-- -----------------------------------------------------------------------------
-- 10. USUARIO
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS usuario (
    codigo_usuario  VARCHAR(50)  PRIMARY KEY,
    contrasena_hash VARCHAR(255) NOT NULL,   -- bcrypt hash
    nombre_completo VARCHAR(200),
    rol             VARCHAR(50)  DEFAULT 'usuario',  -- 'administrador', 'docente', 'usuario'
    estado          CHAR(1)      DEFAULT 'A',
    ultimo_acceso   TIMESTAMP
);

-- -----------------------------------------------------------------------------
-- 11. INSTITUCION
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS institucion (
    id          SERIAL       PRIMARY KEY,
    nombre      VARCHAR(255) NOT NULL,
    codigo_dea  VARCHAR(50),
    direccion   TEXT,
    municipio   VARCHAR(100),
    estado_geo  VARCHAR(100),
    telefono    VARCHAR(20),
    logo        BYTEA
);

-- -----------------------------------------------------------------------------
-- 12. CONSTANCIA
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS constancia (
    id                  SERIAL       PRIMARY KEY,
    numero              VARCHAR(50)  UNIQUE,
    tipo_constancia     VARCHAR(100),
    cedula_estudiante   VARCHAR(20)  REFERENCES estudiante(cedula),
    codigo_ano_escolar  VARCHAR(20)  REFERENCES ano_escolar(codigo),
    codigo_seccion      VARCHAR(20)  REFERENCES seccion(codigo),
    fecha_emision       DATE         DEFAULT CURRENT_DATE,
    motivo_solicitud    TEXT,
    funcionario_emisor  VARCHAR(200),
    codigo_constancia   VARCHAR(100),
    observaciones       TEXT,
    estado              CHAR(1)      DEFAULT 'A'
);

-- -----------------------------------------------------------------------------
-- 13. LABOR_SOCIAL
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS labor_social (
    id                      SERIAL       PRIMARY KEY,
    cedula_estudiante       VARCHAR(20)  NOT NULL REFERENCES estudiante(cedula),
    actividad               VARCHAR(200) NOT NULL,
    institucion_beneficiaria VARCHAR(200),
    ubicacion               VARCHAR(200),
    horas_requeridas        INTEGER      DEFAULT 0,
    horas_cumplidas         INTEGER      DEFAULT 0,
    fecha_inicio            DATE,
    fecha_fin               DATE,
    cumplida                BOOLEAN      DEFAULT FALSE,
    supervisor              VARCHAR(200),
    observaciones           TEXT
);

-- =============================================================================
-- ÍNDICES para optimizar consultas frecuentes
-- =============================================================================
CREATE INDEX IF NOT EXISTS idx_estudiante_cedula    ON estudiante(cedula);
CREATE INDEX IF NOT EXISTS idx_matricula_ano        ON matricula(codigo_ano_escolar);
CREATE INDEX IF NOT EXISTS idx_matricula_seccion    ON matricula(codigo_seccion);
CREATE INDEX IF NOT EXISTS idx_asignacion_seccion   ON asignacion_docente(codigo_seccion, codigo_ano_escolar);
CREATE INDEX IF NOT EXISTS idx_seccion_ano          ON seccion(codigo_ano_escolar);
CREATE INDEX IF NOT EXISTS idx_materia_grado        ON materia(codigo_grado);
CREATE INDEX IF NOT EXISTS idx_labor_social_cedula  ON labor_social(cedula_estudiante);

-- =============================================================================
-- FIN DEL ESQUEMA
-- =============================================================================
