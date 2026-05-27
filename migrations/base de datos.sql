
-- TABLE: ano_escolar
CREATE TABLE public.ano_escolar (
    codigo character varying NOT NULL,
    descripcion character varying,
    ano_inicio integer,
    ano_fin integer,
    fecha_inicio date,
    fecha_fin date,
    estado character(1),
    activo boolean
);;

-- TABLE: asignacion_docente
CREATE TABLE public.asignacion_docente (
    id integer NOT NULL,
    cedula_docente character varying(10),
    codigo_seccion character varying,
    codigo_materia character varying,
    codigo_ano_escolar character varying,
    horas_asignadas integer,
    turno character(1),
    id_imagen integer
);;

-- SEQUENCE: asignacion_docente_id_seq
CREATE SEQUENCE public.asignacion_docente_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;;

-- SEQUENCE OWNED BY: asignacion_docente_id_seq
ALTER SEQUENCE public.asignacion_docente_id_seq OWNED BY public.asignacion_docente.id;;

-- TABLE: boletin
CREATE TABLE public.boletin (
    id integer NOT NULL,
    cedula_estudiante character varying(10),
    codigo_ano_escolar character varying,
    codigo_seccion character varying,
    numero_momento integer,
    promedio_general double precision,
    mencion character(1),
    resultado_final character(1),
    fecha_generacion date,
    tipo_boletin character varying,
    observaciones text,
    CONSTRAINT chk_boletin_cedula_estudiante_formato CHECK (((cedula_estudiante)::text ~ '^[VE]\d{7,9}$'::text))
);;

-- SEQUENCE: boletin_id_seq
CREATE SEQUENCE public.boletin_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;;

-- SEQUENCE OWNED BY: boletin_id_seq
ALTER SEQUENCE public.boletin_id_seq OWNED BY public.boletin.id;;

-- TABLE: citacion
CREATE TABLE public.citacion (
    id integer NOT NULL,
    cedula_representante character varying,
    cedula_estudiante character varying,
    fecha_citacion date,
    hora_citacion time without time zone,
    motivo text,
    asistio boolean,
    fecha_asistencia date,
    acuerdos text,
    observaciones text
);;

-- SEQUENCE: citacion_id_seq
CREATE SEQUENCE public.citacion_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;;

-- SEQUENCE OWNED BY: citacion_id_seq
ALTER SEQUENCE public.citacion_id_seq OWNED BY public.citacion.id;;

-- TABLE: constancia
CREATE TABLE public.constancia (
    numero character varying NOT NULL,
    tipo_constancia character varying,
    cedula_estudiante character varying(10),
    cedula_representante character varying(10),
    codigo_ano_escolar character varying,
    codigo_seccion character varying,
    fecha_emision date,
    motivo_solicitud character varying,
    funcionario_emisor character varying,
    codigo_constancia character varying,
    observaciones text,
    estado character(1),
    CONSTRAINT chk_constancia_cedula_representante_formato CHECK (((cedula_representante)::text ~ '^[VE]\d{7,9}$'::text))
);;

-- TABLE: detalle_boletin
CREATE TABLE public.detalle_boletin (
    id integer NOT NULL,
    id_boletin integer,
    codigo_materia character varying,
    nota_momento1 double precision,
    nota_momento2 double precision,
    nota_momento3 double precision,
    nota_final double precision,
    resultado_materia character(1),
    es_revision boolean,
    observaciones text
);;

-- SEQUENCE: detalle_boletin_id_seq
CREATE SEQUENCE public.detalle_boletin_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;;

-- SEQUENCE OWNED BY: detalle_boletin_id_seq
ALTER SEQUENCE public.detalle_boletin_id_seq OWNED BY public.detalle_boletin.id;;

-- TABLE: detalle_resumen
CREATE TABLE public.detalle_resumen (
    id integer NOT NULL,
    id_resumen integer,
    cedula_estudiante character varying(10),
    codigo_materia character varying,
    nota_momento1 double precision,
    nota_momento2 double precision,
    nota_momento3 double precision,
    nota_final double precision,
    resultado character(1),
    presento boolean,
    es_revision boolean,
    observaciones text,
    CONSTRAINT chk_detalle_resumen_cedula_estudiante_formato CHECK (((cedula_estudiante)::text ~ '^[VE]\d{7,9}$'::text))
);;

-- SEQUENCE: detalle_resumen_id_seq
CREATE SEQUENCE public.detalle_resumen_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;;

-- SEQUENCE OWNED BY: detalle_resumen_id_seq
ALTER SEQUENCE public.detalle_resumen_id_seq OWNED BY public.detalle_resumen.id;;

-- TABLE: estudiante
CREATE TABLE public.estudiante (
    cedula character varying(10) NOT NULL,
    nacionalidad character varying,
    nombres character varying,
    apellidos character varying,
    genero character(1),
    fecha_nacimiento date,
    lugar_nacimiento character varying,
    estado_nacimiento character varying,
    municipio_nacimiento character varying,
    direccion character varying,
    telefono character varying(15),
    correo character varying,
    estatura double precision,
    peso double precision,
    talla_camisa character varying,
    talla_pantalon character varying,
    talla_zapatos character varying,
    condiciones_medicas text,
    medicamentos text,
    plantel_procedencia character varying,
    fecha_ingreso date,
    estado_estudiante character(1),
    fecha_retiro date,
    motivo_retiro character varying,
    CONSTRAINT chk_estudiante_telefono_formato CHECK (((telefono)::text ~ '^\d{11,15}$'::text))
);;

-- TABLE: evaluacion
CREATE TABLE public.evaluacion (
    id integer NOT NULL,
    cedula_estudiante character varying(10),
    codigo_materia character varying,
    codigo_ano_escolar character varying,
    numero_momento integer,
    nota double precision,
    resultado character(1),
    fecha_evaluacion date,
    observaciones text,
    es_revision boolean,
    cedula_docente_evaluador character varying(10),
    fecha_modificacion date,
    motivo_modificacion character varying
);;

-- SEQUENCE: evaluacion_id_seq
CREATE SEQUENCE public.evaluacion_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;;

-- SEQUENCE OWNED BY: evaluacion_id_seq
ALTER SEQUENCE public.evaluacion_id_seq OWNED BY public.evaluacion.id;;

-- TABLE: grado
CREATE TABLE public.grado (
    codigo character varying NOT NULL,
    nombre character varying,
    nivel_educativo character varying,
    numero_ano integer,
    descripcion character varying,
    activo boolean
);;

-- TABLE: grupo_actividad
CREATE TABLE public.grupo_actividad (
    id integer NOT NULL,
    nombre_grupo character varying,
    tipo_actividad character varying,
    descripcion text,
    cedula_coordinador character varying(10),
    codigo_ano_escolar character varying,
    cupos_disponibles integer,
    activo boolean
);;

-- SEQUENCE: grupo_actividad_id_seq
CREATE SEQUENCE public.grupo_actividad_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;;

-- SEQUENCE OWNED BY: grupo_actividad_id_seq
ALTER SEQUENCE public.grupo_actividad_id_seq OWNED BY public.grupo_actividad.id;;

-- TABLE: imagenes
CREATE TABLE public.imagenes (
    id integer NOT NULL,
    nombre_archivo character varying(255) NOT NULL,
    mime_type character varying(50) NOT NULL,
    datos_imagen bytea NOT NULL,
    fecha_subida timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);;

-- SEQUENCE: imagenes_id_seq
CREATE SEQUENCE public.imagenes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;;

-- SEQUENCE OWNED BY: imagenes_id_seq
ALTER SEQUENCE public.imagenes_id_seq OWNED BY public.imagenes.id;;

-- TABLE: institucion
CREATE TABLE public.institucion (
    codigo_dea character varying NOT NULL,
    nombre character varying,
    direccion character varying,
    telefono character varying(15),
    municipio character varying,
    estado character varying,
    zona_educativa character varying,
    director_actual character varying,
    coordinador_academico character varying,
    CONSTRAINT chk_institucion_telefono_formato CHECK (((telefono)::text ~ '^\d{11,15}$'::text))
);;

-- TABLE: labor_social
CREATE TABLE public.labor_social (
    id integer NOT NULL,
    cedula_estudiante character varying,
    actividad character varying,
    institucion_beneficiaria character varying,
    ubicacion character varying,
    horas_requeridas integer,
    horas_cumplidas integer,
    fecha_inicio date,
    fecha_fin date,
    cumplida boolean,
    supervisor character varying,
    observaciones text
);;

-- SEQUENCE: labor_social_id_seq
CREATE SEQUENCE public.labor_social_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;;

-- SEQUENCE OWNED BY: labor_social_id_seq
ALTER SEQUENCE public.labor_social_id_seq OWNED BY public.labor_social.id;;

-- TABLE: login
CREATE TABLE public.login (
    id integer NOT NULL,
    id_usuario integer,
    fecha date,
    hora time without time zone,
    ip_acceso character varying,
    tipo_acceso character(1),
    navegador character varying,
    exitoso boolean
);;

-- SEQUENCE: login_id_seq
CREATE SEQUENCE public.login_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;;

-- SEQUENCE OWNED BY: login_id_seq
ALTER SEQUENCE public.login_id_seq OWNED BY public.login.id;;

-- TABLE: materia
CREATE TABLE public.materia (
    codigo character varying NOT NULL,
    nombre character varying,
    abreviatura character varying,
    area_formacion character varying,
    codigo_grado character varying,
    horas_semanales integer,
    obligatoria boolean,
    tipo_evaluacion character(1),
    se_repara boolean,
    nota_minima_aprobacion double precision,
    estado character(1)
);;

-- TABLE: materia_pendiente
CREATE TABLE public.materia_pendiente (
    id integer NOT NULL,
    cedula_estudiante character varying(10),
    codigo_materia character varying,
    codigo_ano_escolar character varying,
    momento_pendiente integer,
    tipo_pendiente character(1),
    aprobada boolean,
    fecha_presentacion date,
    calificacion_final double precision,
    observaciones text,
    CONSTRAINT chk_materia_pendiente_cedula_estudiante_formato CHECK (((cedula_estudiante)::text ~ '^[VE]\d{7,9}$'::text))
);;

-- SEQUENCE: materia_pendiente_id_seq
CREATE SEQUENCE public.materia_pendiente_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;;

-- SEQUENCE OWNED BY: materia_pendiente_id_seq
ALTER SEQUENCE public.materia_pendiente_id_seq OWNED BY public.materia_pendiente.id;;

-- TABLE: materias
CREATE TABLE public.materias (
    id integer NOT NULL,
    nombre character varying(100) NOT NULL,
    codigo character varying(10) NOT NULL,
    descripcion text,
    horas_semanales integer DEFAULT 4 NOT NULL,
    activo boolean DEFAULT true,
    fecha_creacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);;

-- SEQUENCE: materias_id_seq
CREATE SEQUENCE public.materias_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;;

-- SEQUENCE OWNED BY: materias_id_seq
ALTER SEQUENCE public.materias_id_seq OWNED BY public.materias.id;;

-- TABLE: matricula
CREATE TABLE public.matricula (
    id integer NOT NULL,
    cedula_estudiante character varying(10),
    codigo_ano_escolar character varying,
    codigo_seccion character varying,
    cedula_representante character varying(10),
    fecha_matricula date,
    numero_lista integer,
    condicion_ingreso character(1),
    procedencia character varying,
    ano_que_cursa integer,
    ano_inicio_cursante integer,
    estado_matricula character(1),
    observaciones text,
    fecha_retiro date,
    motivo_retiro character varying,
    foto_estudiante bytea,
    foto_representante bytea
);;

-- SEQUENCE: matricula_id_seq
CREATE SEQUENCE public.matricula_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;;

-- SEQUENCE OWNED BY: matricula_id_seq
ALTER SEQUENCE public.matricula_id_seq OWNED BY public.matricula.id;;

-- TABLE: momento_evaluativo
CREATE TABLE public.momento_evaluativo (
    numero integer NOT NULL,
    codigo_ano_escolar character varying,
    nombre character varying,
    fecha_inicio date,
    fecha_fin date,
    porcentaje double precision,
    estado character(1),
    observaciones text
);;

-- TABLE: participacion_grupo
CREATE TABLE public.participacion_grupo (
    id integer NOT NULL,
    cedula_estudiante character varying(10),
    id_grupo integer,
    fecha_inscripcion date,
    nivel_participacion character varying,
    observaciones text,
    activo boolean
);;

-- SEQUENCE: participacion_grupo_id_seq
CREATE SEQUENCE public.participacion_grupo_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;;

-- SEQUENCE OWNED BY: participacion_grupo_id_seq
ALTER SEQUENCE public.participacion_grupo_id_seq OWNED BY public.participacion_grupo.id;;

-- TABLE: personal
CREATE TABLE public.personal (
    cedula character varying(10) NOT NULL,
    nombres character varying,
    apellidos character varying,
    cargo character varying,
    especialidad character varying,
    telefono character varying(15),
    correo character varying,
    fecha_nacimiento date,
    genero character varying,
    fecha_ingreso date,
    turno character varying,
    carga_horaria integer,
    estado character varying,
    observaciones text,
    CONSTRAINT chk_personal_telefono_formato CHECK (((telefono)::text ~ '^\d{11,15}$'::text))
);;

-- TABLE: representante
CREATE TABLE public.representante (
    cedula character varying(10) NOT NULL,
    nacionalidad character varying,
    nombres character varying,
    apellidos character varying,
    parentesco character varying,
    ocupacion character varying,
    direccion character varying,
    telefono character varying(15),
    correo character varying,
    fecha_nacimiento date,
    genero character(1),
    es_madre boolean,
    es_padre boolean,
    es_representante_legal boolean,
    CONSTRAINT chk_representante_telefono_formato CHECK (((telefono)::text ~ '^\d{11,15}$'::text))
);;

-- TABLE: resumen_final
CREATE TABLE public.resumen_final (
    id integer NOT NULL,
    codigo_ano_escolar character varying,
    codigo_seccion character varying,
    numero_momento integer,
    fecha_generacion date,
    estado character(1),
    tipo_resumen character varying,
    observaciones text
);;

-- SEQUENCE: resumen_final_id_seq
CREATE SEQUENCE public.resumen_final_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;;

-- SEQUENCE OWNED BY: resumen_final_id_seq
ALTER SEQUENCE public.resumen_final_id_seq OWNED BY public.resumen_final.id;;

-- TABLE: revision_academica
CREATE TABLE public.revision_academica (
    id integer NOT NULL,
    cedula_estudiante character varying(10),
    codigo_materia character varying,
    codigo_ano_escolar character varying,
    momento_revision integer,
    tipo_revision character(1),
    fecha_revision date,
    nota_anterior double precision,
    nota_nueva double precision,
    resultado_revision character(1),
    cedula_docente_revisor character varying(10),
    justificacion text,
    estado_revision character(1)
);;

-- SEQUENCE: revision_academica_id_seq
CREATE SEQUENCE public.revision_academica_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;;

-- SEQUENCE OWNED BY: revision_academica_id_seq
ALTER SEQUENCE public.revision_academica_id_seq OWNED BY public.revision_academica.id;;

-- TABLE: seccion
CREATE TABLE public.seccion (
    codigo character varying NOT NULL,
    letra character varying,
    codigo_grado character varying,
    codigo_ano_escolar character varying,
    cedula_docente_guia character varying(10),
    capacidad_maxima integer,
    total_estudiantes integer,
    estudiantes_varones integer,
    estudiantes_hembras integer,
    turno character(1),
    aula_asignada character varying
);;

-- TABLE: titulo
CREATE TABLE public.titulo (
    serial character varying NOT NULL,
    cedula_estudiante character varying(10),
    tipo_titulo character varying,
    fecha_emision date,
    fecha_egreso date,
    libro_registro character varying,
    folio character varying,
    acta character varying,
    promedio_general double precision,
    mencion character(1),
    estado_titulo character(1),
    observaciones text,
    CONSTRAINT chk_titulo_cedula_estudiante_formato CHECK (((cedula_estudiante)::text ~ '^[VE]\d{7,9}$'::text))
);;

-- TABLE: usuario
CREATE TABLE public.usuario (
    id integer NOT NULL,
    codigo_usuario character varying,
    cedula_personal character varying(10),
    rol character varying,
    clave_hash character varying,
    estado character varying(20),
    fecha_creacion date,
    ultimo_acceso date,
    intentos_fallidos integer,
    debe_cambiar_clave boolean DEFAULT false
);;

-- SEQUENCE: usuario_id_seq
CREATE SEQUENCE public.usuario_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;;

-- SEQUENCE OWNED BY: usuario_id_seq
ALTER SEQUENCE public.usuario_id_seq OWNED BY public.usuario.id;;

-- DEFAULT: asignacion_docente id
ALTER TABLE ONLY public.asignacion_docente ALTER COLUMN id SET DEFAULT nextval('public.asignacion_docente_id_seq'::regclass);;

-- DEFAULT: boletin id
ALTER TABLE ONLY public.boletin ALTER COLUMN id SET DEFAULT nextval('public.boletin_id_seq'::regclass);;

-- DEFAULT: citacion id
ALTER TABLE ONLY public.citacion ALTER COLUMN id SET DEFAULT nextval('public.citacion_id_seq'::regclass);;

-- DEFAULT: detalle_boletin id
ALTER TABLE ONLY public.detalle_boletin ALTER COLUMN id SET DEFAULT nextval('public.detalle_boletin_id_seq'::regclass);;

-- DEFAULT: detalle_resumen id
ALTER TABLE ONLY public.detalle_resumen ALTER COLUMN id SET DEFAULT nextval('public.detalle_resumen_id_seq'::regclass);;

-- DEFAULT: evaluacion id
ALTER TABLE ONLY public.evaluacion ALTER COLUMN id SET DEFAULT nextval('public.evaluacion_id_seq'::regclass);;

-- DEFAULT: grupo_actividad id
ALTER TABLE ONLY public.grupo_actividad ALTER COLUMN id SET DEFAULT nextval('public.grupo_actividad_id_seq'::regclass);;

-- DEFAULT: imagenes id
ALTER TABLE ONLY public.imagenes ALTER COLUMN id SET DEFAULT nextval('public.imagenes_id_seq'::regclass);;

-- DEFAULT: labor_social id
ALTER TABLE ONLY public.labor_social ALTER COLUMN id SET DEFAULT nextval('public.labor_social_id_seq'::regclass);;

-- DEFAULT: login id
ALTER TABLE ONLY public.login ALTER COLUMN id SET DEFAULT nextval('public.login_id_seq'::regclass);;

-- DEFAULT: materia_pendiente id
ALTER TABLE ONLY public.materia_pendiente ALTER COLUMN id SET DEFAULT nextval('public.materia_pendiente_id_seq'::regclass);;

-- DEFAULT: materias id
ALTER TABLE ONLY public.materias ALTER COLUMN id SET DEFAULT nextval('public.materias_id_seq'::regclass);;

-- DEFAULT: matricula id
ALTER TABLE ONLY public.matricula ALTER COLUMN id SET DEFAULT nextval('public.matricula_id_seq'::regclass);;

-- DEFAULT: participacion_grupo id
ALTER TABLE ONLY public.participacion_grupo ALTER COLUMN id SET DEFAULT nextval('public.participacion_grupo_id_seq'::regclass);;

-- DEFAULT: resumen_final id
ALTER TABLE ONLY public.resumen_final ALTER COLUMN id SET DEFAULT nextval('public.resumen_final_id_seq'::regclass);;

-- DEFAULT: revision_academica id
ALTER TABLE ONLY public.revision_academica ALTER COLUMN id SET DEFAULT nextval('public.revision_academica_id_seq'::regclass);;

-- DEFAULT: usuario id
ALTER TABLE ONLY public.usuario ALTER COLUMN id SET DEFAULT nextval('public.usuario_id_seq'::regclass);;

-- SEQUENCE SET: asignacion_docente_id_seq
SELECT pg_catalog.setval('public.asignacion_docente_id_seq', 21, true);;

-- SEQUENCE SET: boletin_id_seq
SELECT pg_catalog.setval('public.boletin_id_seq', 1, false);;

-- SEQUENCE SET: citacion_id_seq
SELECT pg_catalog.setval('public.citacion_id_seq', 1, false);;

-- SEQUENCE SET: detalle_boletin_id_seq
SELECT pg_catalog.setval('public.detalle_boletin_id_seq', 1, false);;

-- SEQUENCE SET: detalle_resumen_id_seq
SELECT pg_catalog.setval('public.detalle_resumen_id_seq', 1, false);;

-- SEQUENCE SET: evaluacion_id_seq
SELECT pg_catalog.setval('public.evaluacion_id_seq', 28, true);;

-- SEQUENCE SET: grupo_actividad_id_seq
SELECT pg_catalog.setval('public.grupo_actividad_id_seq', 5, true);;

-- SEQUENCE SET: imagenes_id_seq
SELECT pg_catalog.setval('public.imagenes_id_seq', 1, true);;

-- SEQUENCE SET: labor_social_id_seq
SELECT pg_catalog.setval('public.labor_social_id_seq', 1, true);;

-- SEQUENCE SET: login_id_seq
SELECT pg_catalog.setval('public.login_id_seq', 1, false);;

-- SEQUENCE SET: materia_pendiente_id_seq
SELECT pg_catalog.setval('public.materia_pendiente_id_seq', 1, false);;

-- SEQUENCE SET: materias_id_seq
SELECT pg_catalog.setval('public.materias_id_seq', 14, true);;

-- SEQUENCE SET: matricula_id_seq
SELECT pg_catalog.setval('public.matricula_id_seq', 4, true);;

-- SEQUENCE SET: participacion_grupo_id_seq
SELECT pg_catalog.setval('public.participacion_grupo_id_seq', 5, true);;

-- SEQUENCE SET: resumen_final_id_seq
SELECT pg_catalog.setval('public.resumen_final_id_seq', 1, false);;

-- SEQUENCE SET: revision_academica_id_seq
SELECT pg_catalog.setval('public.revision_academica_id_seq', 14, true);;

-- SEQUENCE SET: usuario_id_seq
SELECT pg_catalog.setval('public.usuario_id_seq', 9, true);;

-- CONSTRAINT: ano_escolar ano_escolar_pkey
ALTER TABLE ONLY public.ano_escolar
    ADD CONSTRAINT ano_escolar_pkey PRIMARY KEY (codigo);;

-- CONSTRAINT: asignacion_docente asignacion_docente_pkey
ALTER TABLE ONLY public.asignacion_docente
    ADD CONSTRAINT asignacion_docente_pkey PRIMARY KEY (id);;

-- CONSTRAINT: boletin boletin_pkey
ALTER TABLE ONLY public.boletin
    ADD CONSTRAINT boletin_pkey PRIMARY KEY (id);;

-- CONSTRAINT: citacion citacion_pkey
ALTER TABLE ONLY public.citacion
    ADD CONSTRAINT citacion_pkey PRIMARY KEY (id);;

-- CONSTRAINT: constancia constancia_pkey
ALTER TABLE ONLY public.constancia
    ADD CONSTRAINT constancia_pkey PRIMARY KEY (numero);;

-- CONSTRAINT: detalle_boletin detalle_boletin_pkey
ALTER TABLE ONLY public.detalle_boletin
    ADD CONSTRAINT detalle_boletin_pkey PRIMARY KEY (id);;

-- CONSTRAINT: detalle_resumen detalle_resumen_pkey
ALTER TABLE ONLY public.detalle_resumen
    ADD CONSTRAINT detalle_resumen_pkey PRIMARY KEY (id);;

-- CONSTRAINT: estudiante estudiante_pkey
ALTER TABLE ONLY public.estudiante
    ADD CONSTRAINT estudiante_pkey PRIMARY KEY (cedula);;

-- CONSTRAINT: evaluacion evaluacion_pkey
ALTER TABLE ONLY public.evaluacion
    ADD CONSTRAINT evaluacion_pkey PRIMARY KEY (id);;

-- CONSTRAINT: grado grado_pkey
ALTER TABLE ONLY public.grado
    ADD CONSTRAINT grado_pkey PRIMARY KEY (codigo);;

-- CONSTRAINT: grupo_actividad grupo_actividad_pkey
ALTER TABLE ONLY public.grupo_actividad
    ADD CONSTRAINT grupo_actividad_pkey PRIMARY KEY (id);;

-- CONSTRAINT: imagenes imagenes_pkey
ALTER TABLE ONLY public.imagenes
    ADD CONSTRAINT imagenes_pkey PRIMARY KEY (id);;

-- CONSTRAINT: institucion institucion_pkey
ALTER TABLE ONLY public.institucion
    ADD CONSTRAINT institucion_pkey PRIMARY KEY (codigo_dea);;

-- CONSTRAINT: labor_social labor_social_pkey
ALTER TABLE ONLY public.labor_social
    ADD CONSTRAINT labor_social_pkey PRIMARY KEY (id);;

-- CONSTRAINT: login login_pkey
ALTER TABLE ONLY public.login
    ADD CONSTRAINT login_pkey PRIMARY KEY (id);;

-- CONSTRAINT: materia_pendiente materia_pendiente_pkey
ALTER TABLE ONLY public.materia_pendiente
    ADD CONSTRAINT materia_pendiente_pkey PRIMARY KEY (id);;

-- CONSTRAINT: materia materia_pkey
ALTER TABLE ONLY public.materia
    ADD CONSTRAINT materia_pkey PRIMARY KEY (codigo);;

-- CONSTRAINT: materias materias_codigo_key
ALTER TABLE ONLY public.materias
    ADD CONSTRAINT materias_codigo_key UNIQUE (codigo);;

-- CONSTRAINT: materias materias_nombre_key
ALTER TABLE ONLY public.materias
    ADD CONSTRAINT materias_nombre_key UNIQUE (nombre);;

-- CONSTRAINT: materias materias_pkey
ALTER TABLE ONLY public.materias
    ADD CONSTRAINT materias_pkey PRIMARY KEY (id);;

-- CONSTRAINT: matricula matricula_pkey
ALTER TABLE ONLY public.matricula
    ADD CONSTRAINT matricula_pkey PRIMARY KEY (id);;

-- CONSTRAINT: momento_evaluativo momento_evaluativo_pkey
ALTER TABLE ONLY public.momento_evaluativo
    ADD CONSTRAINT momento_evaluativo_pkey PRIMARY KEY (numero);;

-- CONSTRAINT: participacion_grupo participacion_grupo_pkey
ALTER TABLE ONLY public.participacion_grupo
    ADD CONSTRAINT participacion_grupo_pkey PRIMARY KEY (id);;

-- CONSTRAINT: personal personal_pkey
ALTER TABLE ONLY public.personal
    ADD CONSTRAINT personal_pkey PRIMARY KEY (cedula);;

-- CONSTRAINT: prueba login prueba login_pkey
ALTER TABLE ONLY public."prueba login"
    ADD CONSTRAINT "prueba login_pkey" PRIMARY KEY (id);;

-- CONSTRAINT: representante representante_pkey
ALTER TABLE ONLY public.representante
    ADD CONSTRAINT representante_pkey PRIMARY KEY (cedula);;

-- CONSTRAINT: resumen_final resumen_final_pkey
ALTER TABLE ONLY public.resumen_final
    ADD CONSTRAINT resumen_final_pkey PRIMARY KEY (id);;

-- CONSTRAINT: revision_academica revision_academica_pkey
ALTER TABLE ONLY public.revision_academica
    ADD CONSTRAINT revision_academica_pkey PRIMARY KEY (id);;

-- CONSTRAINT: seccion seccion_pkey
ALTER TABLE ONLY public.seccion
    ADD CONSTRAINT seccion_pkey PRIMARY KEY (codigo);;

-- CONSTRAINT: titulo titulo_pkey
ALTER TABLE ONLY public.titulo
    ADD CONSTRAINT titulo_pkey PRIMARY KEY (serial);;

-- CONSTRAINT: usuario usuario_pkey
ALTER TABLE ONLY public.usuario
    ADD CONSTRAINT usuario_pkey PRIMARY KEY (id);;

-- FK CONSTRAINT: asignacion_docente asignacion_docente_cedula_docente_fkey
ALTER TABLE ONLY public.asignacion_docente
    ADD CONSTRAINT asignacion_docente_cedula_docente_fkey FOREIGN KEY (cedula_docente) REFERENCES public.personal(cedula);;

-- FK CONSTRAINT: asignacion_docente asignacion_docente_codigo_ano_escolar_fkey
ALTER TABLE ONLY public.asignacion_docente
    ADD CONSTRAINT asignacion_docente_codigo_ano_escolar_fkey FOREIGN KEY (codigo_ano_escolar) REFERENCES public.ano_escolar(codigo);;

-- FK CONSTRAINT: asignacion_docente asignacion_docente_codigo_materia_fkey
ALTER TABLE ONLY public.asignacion_docente
    ADD CONSTRAINT asignacion_docente_codigo_materia_fkey FOREIGN KEY (codigo_materia) REFERENCES public.materia(codigo);;

-- FK CONSTRAINT: asignacion_docente asignacion_docente_codigo_seccion_fkey
ALTER TABLE ONLY public.asignacion_docente
    ADD CONSTRAINT asignacion_docente_codigo_seccion_fkey FOREIGN KEY (codigo_seccion) REFERENCES public.seccion(codigo);;

-- FK CONSTRAINT: boletin boletin_cedula_estudiante_fkey
ALTER TABLE ONLY public.boletin
    ADD CONSTRAINT boletin_cedula_estudiante_fkey FOREIGN KEY (cedula_estudiante) REFERENCES public.estudiante(cedula);;

-- FK CONSTRAINT: boletin boletin_codigo_ano_escolar_fkey
ALTER TABLE ONLY public.boletin
    ADD CONSTRAINT boletin_codigo_ano_escolar_fkey FOREIGN KEY (codigo_ano_escolar) REFERENCES public.ano_escolar(codigo);;

-- FK CONSTRAINT: boletin boletin_codigo_seccion_fkey
ALTER TABLE ONLY public.boletin
    ADD CONSTRAINT boletin_codigo_seccion_fkey FOREIGN KEY (codigo_seccion) REFERENCES public.seccion(codigo);;

-- FK CONSTRAINT: citacion citacion_cedula_estudiante_fkey
ALTER TABLE ONLY public.citacion
    ADD CONSTRAINT citacion_cedula_estudiante_fkey FOREIGN KEY (cedula_estudiante) REFERENCES public.estudiante(cedula);;

-- FK CONSTRAINT: citacion citacion_cedula_representante_fkey
ALTER TABLE ONLY public.citacion
    ADD CONSTRAINT citacion_cedula_representante_fkey FOREIGN KEY (cedula_representante) REFERENCES public.representante(cedula);;

-- FK CONSTRAINT: constancia constancia_cedula_estudiante_fkey
ALTER TABLE ONLY public.constancia
    ADD CONSTRAINT constancia_cedula_estudiante_fkey FOREIGN KEY (cedula_estudiante) REFERENCES public.estudiante(cedula);;

-- FK CONSTRAINT: constancia constancia_cedula_representante_fkey
ALTER TABLE ONLY public.constancia
    ADD CONSTRAINT constancia_cedula_representante_fkey FOREIGN KEY (cedula_representante) REFERENCES public.representante(cedula);;

-- FK CONSTRAINT: constancia constancia_codigo_ano_escolar_fkey
ALTER TABLE ONLY public.constancia
    ADD CONSTRAINT constancia_codigo_ano_escolar_fkey FOREIGN KEY (codigo_ano_escolar) REFERENCES public.ano_escolar(codigo);;

-- FK CONSTRAINT: constancia constancia_codigo_seccion_fkey
ALTER TABLE ONLY public.constancia
    ADD CONSTRAINT constancia_codigo_seccion_fkey FOREIGN KEY (codigo_seccion) REFERENCES public.seccion(codigo);;

-- FK CONSTRAINT: detalle_boletin detalle_boletin_codigo_materia_fkey
ALTER TABLE ONLY public.detalle_boletin
    ADD CONSTRAINT detalle_boletin_codigo_materia_fkey FOREIGN KEY (codigo_materia) REFERENCES public.materia(codigo);;

-- FK CONSTRAINT: detalle_boletin detalle_boletin_id_boletin_fkey
ALTER TABLE ONLY public.detalle_boletin
    ADD CONSTRAINT detalle_boletin_id_boletin_fkey FOREIGN KEY (id_boletin) REFERENCES public.boletin(id);;

-- FK CONSTRAINT: detalle_resumen detalle_resumen_cedula_estudiante_fkey
ALTER TABLE ONLY public.detalle_resumen
    ADD CONSTRAINT detalle_resumen_cedula_estudiante_fkey FOREIGN KEY (cedula_estudiante) REFERENCES public.estudiante(cedula);;

-- FK CONSTRAINT: detalle_resumen detalle_resumen_codigo_materia_fkey
ALTER TABLE ONLY public.detalle_resumen
    ADD CONSTRAINT detalle_resumen_codigo_materia_fkey FOREIGN KEY (codigo_materia) REFERENCES public.materia(codigo);;

-- FK CONSTRAINT: detalle_resumen detalle_resumen_id_resumen_fkey
ALTER TABLE ONLY public.detalle_resumen
    ADD CONSTRAINT detalle_resumen_id_resumen_fkey FOREIGN KEY (id_resumen) REFERENCES public.resumen_final(id);;

-- FK CONSTRAINT: evaluacion evaluacion_cedula_docente_evaluador_fkey
ALTER TABLE ONLY public.evaluacion
    ADD CONSTRAINT evaluacion_cedula_docente_evaluador_fkey FOREIGN KEY (cedula_docente_evaluador) REFERENCES public.personal(cedula);;

-- FK CONSTRAINT: evaluacion evaluacion_cedula_estudiante_fkey
ALTER TABLE ONLY public.evaluacion
    ADD CONSTRAINT evaluacion_cedula_estudiante_fkey FOREIGN KEY (cedula_estudiante) REFERENCES public.estudiante(cedula);;

-- FK CONSTRAINT: evaluacion evaluacion_codigo_ano_escolar_fkey
ALTER TABLE ONLY public.evaluacion
    ADD CONSTRAINT evaluacion_codigo_ano_escolar_fkey FOREIGN KEY (codigo_ano_escolar) REFERENCES public.ano_escolar(codigo);;

-- FK CONSTRAINT: evaluacion evaluacion_codigo_materia_fkey
ALTER TABLE ONLY public.evaluacion
    ADD CONSTRAINT evaluacion_codigo_materia_fkey FOREIGN KEY (codigo_materia) REFERENCES public.materia(codigo);;

-- FK CONSTRAINT: asignacion_docente fk_asignacion_docente_imagen
ALTER TABLE ONLY public.asignacion_docente
    ADD CONSTRAINT fk_asignacion_docente_imagen FOREIGN KEY (id_imagen) REFERENCES public.imagenes(id);;

-- FK CONSTRAINT: grupo_actividad grupo_actividad_cedula_coordinador_fkey
ALTER TABLE ONLY public.grupo_actividad
    ADD CONSTRAINT grupo_actividad_cedula_coordinador_fkey FOREIGN KEY (cedula_coordinador) REFERENCES public.personal(cedula);;

-- FK CONSTRAINT: grupo_actividad grupo_actividad_codigo_ano_escolar_fkey
ALTER TABLE ONLY public.grupo_actividad
    ADD CONSTRAINT grupo_actividad_codigo_ano_escolar_fkey FOREIGN KEY (codigo_ano_escolar) REFERENCES public.ano_escolar(codigo);;

-- FK CONSTRAINT: labor_social labor_social_cedula_estudiante_fkey
ALTER TABLE ONLY public.labor_social
    ADD CONSTRAINT labor_social_cedula_estudiante_fkey FOREIGN KEY (cedula_estudiante) REFERENCES public.estudiante(cedula);;

-- FK CONSTRAINT: login login_id_usuario_fkey
ALTER TABLE ONLY public.login
    ADD CONSTRAINT login_id_usuario_fkey FOREIGN KEY (id_usuario) REFERENCES public.usuario(id);;

-- FK CONSTRAINT: materia materia_codigo_grado_fkey
ALTER TABLE ONLY public.materia
    ADD CONSTRAINT materia_codigo_grado_fkey FOREIGN KEY (codigo_grado) REFERENCES public.grado(codigo);;

-- FK CONSTRAINT: materia_pendiente materia_pendiente_cedula_estudiante_fkey
ALTER TABLE ONLY public.materia_pendiente
    ADD CONSTRAINT materia_pendiente_cedula_estudiante_fkey FOREIGN KEY (cedula_estudiante) REFERENCES public.estudiante(cedula);;

-- FK CONSTRAINT: materia_pendiente materia_pendiente_codigo_ano_escolar_fkey
ALTER TABLE ONLY public.materia_pendiente
    ADD CONSTRAINT materia_pendiente_codigo_ano_escolar_fkey FOREIGN KEY (codigo_ano_escolar) REFERENCES public.ano_escolar(codigo);;

-- FK CONSTRAINT: materia_pendiente materia_pendiente_codigo_materia_fkey
ALTER TABLE ONLY public.materia_pendiente
    ADD CONSTRAINT materia_pendiente_codigo_materia_fkey FOREIGN KEY (codigo_materia) REFERENCES public.materia(codigo);;

-- FK CONSTRAINT: matricula matricula_cedula_estudiante_fkey
ALTER TABLE ONLY public.matricula
    ADD CONSTRAINT matricula_cedula_estudiante_fkey FOREIGN KEY (cedula_estudiante) REFERENCES public.estudiante(cedula);;

-- FK CONSTRAINT: matricula matricula_cedula_representante_fkey
ALTER TABLE ONLY public.matricula
    ADD CONSTRAINT matricula_cedula_representante_fkey FOREIGN KEY (cedula_representante) REFERENCES public.representante(cedula);;

-- FK CONSTRAINT: matricula matricula_codigo_ano_escolar_fkey
ALTER TABLE ONLY public.matricula
    ADD CONSTRAINT matricula_codigo_ano_escolar_fkey FOREIGN KEY (codigo_ano_escolar) REFERENCES public.ano_escolar(codigo);;

-- FK CONSTRAINT: matricula matricula_codigo_seccion_fkey
ALTER TABLE ONLY public.matricula
    ADD CONSTRAINT matricula_codigo_seccion_fkey FOREIGN KEY (codigo_seccion) REFERENCES public.seccion(codigo);;

-- FK CONSTRAINT: momento_evaluativo momento_evaluativo_codigo_ano_escolar_fkey
ALTER TABLE ONLY public.momento_evaluativo
    ADD CONSTRAINT momento_evaluativo_codigo_ano_escolar_fkey FOREIGN KEY (codigo_ano_escolar) REFERENCES public.ano_escolar(codigo);;

-- FK CONSTRAINT: participacion_grupo participacion_grupo_cedula_estudiante_fkey
ALTER TABLE ONLY public.participacion_grupo
    ADD CONSTRAINT participacion_grupo_cedula_estudiante_fkey FOREIGN KEY (cedula_estudiante) REFERENCES public.estudiante(cedula);;

-- FK CONSTRAINT: participacion_grupo participacion_grupo_id_grupo_fkey
ALTER TABLE ONLY public.participacion_grupo
    ADD CONSTRAINT participacion_grupo_id_grupo_fkey FOREIGN KEY (id_grupo) REFERENCES public.grupo_actividad(id);;

-- FK CONSTRAINT: resumen_final resumen_final_codigo_ano_escolar_fkey
ALTER TABLE ONLY public.resumen_final
    ADD CONSTRAINT resumen_final_codigo_ano_escolar_fkey FOREIGN KEY (codigo_ano_escolar) REFERENCES public.ano_escolar(codigo);;

-- FK CONSTRAINT: resumen_final resumen_final_codigo_seccion_fkey
ALTER TABLE ONLY public.resumen_final
    ADD CONSTRAINT resumen_final_codigo_seccion_fkey FOREIGN KEY (codigo_seccion) REFERENCES public.seccion(codigo);;

-- FK CONSTRAINT: revision_academica revision_academica_cedula_docente_revisor_fkey
ALTER TABLE ONLY public.revision_academica
    ADD CONSTRAINT revision_academica_cedula_docente_revisor_fkey FOREIGN KEY (cedula_docente_revisor) REFERENCES public.personal(cedula);;

-- FK CONSTRAINT: revision_academica revision_academica_cedula_estudiante_fkey
ALTER TABLE ONLY public.revision_academica
    ADD CONSTRAINT revision_academica_cedula_estudiante_fkey FOREIGN KEY (cedula_estudiante) REFERENCES public.estudiante(cedula);;

-- FK CONSTRAINT: revision_academica revision_academica_codigo_ano_escolar_fkey
ALTER TABLE ONLY public.revision_academica
    ADD CONSTRAINT revision_academica_codigo_ano_escolar_fkey FOREIGN KEY (codigo_ano_escolar) REFERENCES public.ano_escolar(codigo);;

-- FK CONSTRAINT: revision_academica revision_academica_codigo_materia_fkey
ALTER TABLE ONLY public.revision_academica
    ADD CONSTRAINT revision_academica_codigo_materia_fkey FOREIGN KEY (codigo_materia) REFERENCES public.materia(codigo);;

-- FK CONSTRAINT: seccion seccion_cedula_docente_guia_fkey
ALTER TABLE ONLY public.seccion
    ADD CONSTRAINT seccion_cedula_docente_guia_fkey FOREIGN KEY (cedula_docente_guia) REFERENCES public.personal(cedula);;

-- FK CONSTRAINT: seccion seccion_codigo_ano_escolar_fkey
ALTER TABLE ONLY public.seccion
    ADD CONSTRAINT seccion_codigo_ano_escolar_fkey FOREIGN KEY (codigo_ano_escolar) REFERENCES public.ano_escolar(codigo);;

-- FK CONSTRAINT: seccion seccion_codigo_grado_fkey
ALTER TABLE ONLY public.seccion
    ADD CONSTRAINT seccion_codigo_grado_fkey FOREIGN KEY (codigo_grado) REFERENCES public.grado(codigo);;

-- FK CONSTRAINT: titulo titulo_cedula_estudiante_fkey
ALTER TABLE ONLY public.titulo
    ADD CONSTRAINT titulo_cedula_estudiante_fkey FOREIGN KEY (cedula_estudiante) REFERENCES public.estudiante(cedula);;
