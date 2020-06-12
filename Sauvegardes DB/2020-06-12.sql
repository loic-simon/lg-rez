--
-- PostgreSQL database dump
--

-- Dumped from database version 12.2
-- Dumped by pg_dump version 12.0

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: public; Type: SCHEMA; Schema: -; Owner: lg-rez
--

CREATE SCHEMA public;


ALTER SCHEMA public OWNER TO "lg-rez";

--
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: lg-rez
--

COMMENT ON SCHEMA public IS 'standard public schema';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: actions; Type: TABLE; Schema: public; Owner: lg-rez
--

CREATE TABLE public.actions (
    _id integer NOT NULL,
    player_id bigint NOT NULL,
    action character varying(32) NOT NULL,
    trigger_debut character varying(32),
    trigger_fin character varying(32),
    instant boolean,
    heure_debut time without time zone,
    heure_fin time without time zone,
    cooldown integer NOT NULL,
    charges integer,
    refill character varying(32),
    lieu character varying(32),
    interaction_notaire character varying(32),
    interaction_gardien character varying(32),
    mage character varying(100),
    changement_cible boolean,
    _decision character varying(200)
);


ALTER TABLE public.actions OWNER TO "lg-rez";

--
-- Name: actions__id_seq; Type: SEQUENCE; Schema: public; Owner: lg-rez
--

CREATE SEQUENCE public.actions__id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.actions__id_seq OWNER TO "lg-rez";

--
-- Name: actions__id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: lg-rez
--

ALTER SEQUENCE public.actions__id_seq OWNED BY public.actions._id;


--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: lg-rez
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO "lg-rez";

--
-- Name: base_actions; Type: TABLE; Schema: public; Owner: lg-rez
--

CREATE TABLE public.base_actions (
    action character varying(32) NOT NULL,
    trigger_debut character varying(32),
    trigger_fin character varying(32),
    instant boolean,
    heure_debut time without time zone,
    heure_fin time without time zone,
    base_cooldown integer NOT NULL,
    base_charges integer,
    refill character varying(32),
    lieu character varying(32),
    interaction_notaire character varying(32),
    interaction_gardien character varying(32),
    mage character varying(100),
    changement_cible boolean
);


ALTER TABLE public.base_actions OWNER TO "lg-rez";

--
-- Name: base_actions_roles; Type: TABLE; Schema: public; Owner: lg-rez
--

CREATE TABLE public.base_actions_roles (
    id integer NOT NULL,
    role character varying(32) NOT NULL,
    action character varying(32) NOT NULL
);


ALTER TABLE public.base_actions_roles OWNER TO "lg-rez";

--
-- Name: base_actions_roles_id_seq; Type: SEQUENCE; Schema: public; Owner: lg-rez
--

CREATE SEQUENCE public.base_actions_roles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.base_actions_roles_id_seq OWNER TO "lg-rez";

--
-- Name: base_actions_roles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: lg-rez
--

ALTER SEQUENCE public.base_actions_roles_id_seq OWNED BY public.base_actions_roles.id;


--
-- Name: joueurs; Type: TABLE; Schema: public; Owner: lg-rez
--

CREATE TABLE public.joueurs (
    discord_id bigint NOT NULL,
    _chan_id bigint NOT NULL,
    nom character varying(32) NOT NULL,
    chambre character varying(200) NOT NULL,
    statut character varying(32) NOT NULL,
    role character varying(32) NOT NULL,
    camp character varying(32) NOT NULL,
    votant_village boolean NOT NULL,
    votant_loups boolean NOT NULL,
    role_actif boolean,
    _vote_condamne character varying(200),
    _vote_maire character varying(200),
    _vote_loups character varying(200)
);


ALTER TABLE public.joueurs OWNER TO "lg-rez";

--
-- Name: joueurs_discord_id_seq; Type: SEQUENCE; Schema: public; Owner: lg-rez
--

CREATE SEQUENCE public.joueurs_discord_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.joueurs_discord_id_seq OWNER TO "lg-rez";

--
-- Name: joueurs_discord_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: lg-rez
--

ALTER SEQUENCE public.joueurs_discord_id_seq OWNED BY public.joueurs.discord_id;


--
-- Name: reactions; Type: TABLE; Schema: public; Owner: lg-rez
--

CREATE TABLE public.reactions (
    id integer NOT NULL,
    reponse character varying(2000) NOT NULL
);


ALTER TABLE public.reactions OWNER TO "lg-rez";

--
-- Name: reactions_id_seq; Type: SEQUENCE; Schema: public; Owner: lg-rez
--

CREATE SEQUENCE public.reactions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.reactions_id_seq OWNER TO "lg-rez";

--
-- Name: reactions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: lg-rez
--

ALTER SEQUENCE public.reactions_id_seq OWNED BY public.reactions.id;


--
-- Name: roles; Type: TABLE; Schema: public; Owner: lg-rez
--

CREATE TABLE public.roles (
    slug character varying(32) NOT NULL,
    prefixe character varying(8) NOT NULL,
    nom character varying(32) NOT NULL,
    camp character varying(32) NOT NULL,
    description_courte character varying(140) NOT NULL,
    description_longue character varying(2000) NOT NULL
);


ALTER TABLE public.roles OWNER TO "lg-rez";

--
-- Name: triggers; Type: TABLE; Schema: public; Owner: lg-rez
--

CREATE TABLE public.triggers (
    id integer NOT NULL,
    trigger character varying(500) NOT NULL,
    reac_id integer NOT NULL
);


ALTER TABLE public.triggers OWNER TO "lg-rez";

--
-- Name: triggers_id_seq; Type: SEQUENCE; Schema: public; Owner: lg-rez
--

CREATE SEQUENCE public.triggers_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.triggers_id_seq OWNER TO "lg-rez";

--
-- Name: triggers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: lg-rez
--

ALTER SEQUENCE public.triggers_id_seq OWNED BY public.triggers.id;


--
-- Name: actions _id; Type: DEFAULT; Schema: public; Owner: lg-rez
--

ALTER TABLE ONLY public.actions ALTER COLUMN _id SET DEFAULT nextval('public.actions__id_seq'::regclass);


--
-- Name: base_actions_roles id; Type: DEFAULT; Schema: public; Owner: lg-rez
--

ALTER TABLE ONLY public.base_actions_roles ALTER COLUMN id SET DEFAULT nextval('public.base_actions_roles_id_seq'::regclass);


--
-- Name: joueurs discord_id; Type: DEFAULT; Schema: public; Owner: lg-rez
--

ALTER TABLE ONLY public.joueurs ALTER COLUMN discord_id SET DEFAULT nextval('public.joueurs_discord_id_seq'::regclass);


--
-- Name: reactions id; Type: DEFAULT; Schema: public; Owner: lg-rez
--

ALTER TABLE ONLY public.reactions ALTER COLUMN id SET DEFAULT nextval('public.reactions_id_seq'::regclass);


--
-- Name: triggers id; Type: DEFAULT; Schema: public; Owner: lg-rez
--

ALTER TABLE ONLY public.triggers ALTER COLUMN id SET DEFAULT nextval('public.triggers_id_seq'::regclass);


--
-- Data for Name: actions; Type: TABLE DATA; Schema: public; Owner: lg-rez
--

INSERT INTO public.actions VALUES (2, 264482202966818825, 'bonsoir-euw', 'temporel', NULL, true, '19:00:00', NULL, 0, 1, 'weekends', NULL, NULL, NULL, NULL, false, NULL);
INSERT INTO public.actions VALUES (1, 264482202966818825, 'voyante-au', NULL, NULL, false, NULL, NULL, 0, NULL, NULL, NULL, NULL, NULL, NULL, false, 'j''adore les pâtes');


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: lg-rez
--



--
-- Data for Name: base_actions; Type: TABLE DATA; Schema: public; Owner: lg-rez
--

INSERT INTO public.base_actions VALUES ('rebouteux-au', 'mot_mjs', 'delta', true, NULL, '01:00:00', 0, 1, 'forgeron', 'Distance', 'Non', 'Non', 'Pas d''action', NULL);
INSERT INTO public.base_actions VALUES ('juge-au', 'mot_mjs', 'delta', true, NULL, '00:30:00', 0, 1, 'forgeron, rebouteux', 'Distance', 'Non', 'Non', 'Pas d''action', NULL);
INSERT INTO public.base_actions VALUES ('servante-au', 'mot_mjs', 'delta', true, NULL, '01:00:00', 0, 1, NULL, 'Distance', 'Non', 'Non', 'Pas d''action', NULL);
INSERT INTO public.base_actions VALUES ('chatelain-au', 'close_cond', 'delta', true, NULL, '00:10:00', 0, 1, 'forgeron, rebouteux', 'Distance', 'Non', 'Non', 'Pas d''action car de jour', NULL);
INSERT INTO public.base_actions VALUES ('tavernier-au', 'temporel', 'temporel', NULL, '19:00:00', '20:00:00', 0, NULL, NULL, 'Lieu', 'Oui', 'Taverne', 'Pas d''action', true);
INSERT INTO public.base_actions VALUES ('voyante-au', 'temporel', 'temporel', NULL, '19:00:00', '22:00:00', 0, NULL, NULL, 'Distance', 'Oui', 'Non', 'Le mage obtient l''info sur le rôle de B', false);
INSERT INTO public.base_actions VALUES ('maitrexo-protection', 'temporel', 'temporel', NULL, '19:00:00', '22:00:00', 1, NULL, NULL, 'Distance', 'Oui', 'Conditionnel', NULL, NULL);
INSERT INTO public.base_actions VALUES ('maitrexo-sondage', 'temporel', 'temporel', NULL, '19:00:00', '22:00:00', 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO public.base_actions VALUES ('apprexo-au', 'temporel', 'temporel', NULL, '19:00:00', '22:00:00', 0, NULL, NULL, 'Distance', 'Oui', 'Oui', 'Ne tue pas le MV, et entre en contact avec lui', false);
INSERT INTO public.base_actions VALUES ('protecteur-au', 'temporel', 'temporel', NULL, '19:00:00', '22:00:00', 0, NULL, NULL, 'Distance', 'Oui', 'Non', 'B protégé', true);
INSERT INTO public.base_actions VALUES ('maquerelle-au', 'temporel', 'temporel', NULL, '19:00:00', '22:00:00', 0, NULL, NULL, 'Lieu', 'Oui', 'MaisonClose', 'B maquerellé avec C aléatoire', true);
INSERT INTO public.base_actions VALUES ('ludopathe-au', 'temporel', 'temporel', NULL, '19:00:00', '22:00:00', 0, NULL, NULL, 'Conditionnel', 'Conditionnel', 'Conditionnel', 'B devient la cible', NULL);
INSERT INTO public.base_actions VALUES ('espion-au', 'temporel', 'temporel', NULL, '19:00:00', '22:00:00', 0, NULL, NULL, 'Physique', 'Oui', 'Conditionnel', 'Rapport sur B pour le mage', false);
INSERT INTO public.base_actions VALUES ('tailleur-au', 'temporel', 'temporel', NULL, '19:00:00', '22:00:00', 0, NULL, NULL, 'Physique', 'Oui', 'Précis', 'B menhiré', true);
INSERT INTO public.base_actions VALUES ('gardien-au', 'temporel', 'temporel', NULL, '19:00:00', '22:00:00', 1, NULL, NULL, 'Distance', 'Oui', NULL, 'Le mage connait les actions de B pendant la nuit (ex: B est allé chez C)', NULL);
INSERT INTO public.base_actions VALUES ('chasseur-detect', 'temporel', 'temporel', NULL, '19:00:00', '09:00:00', 0, 1, 'forgeron, rebouteux', 'Physique', 'Oui', 'Oui', 'Le mage reçoit le nombre de loups', NULL);
INSERT INTO public.base_actions VALUES ('chasseur-mort', 'mort', 'delta', true, NULL, '00:10:00', 0, 1, NULL, 'Public', 'Non', 'Non', 'Pas possible', NULL);
INSERT INTO public.base_actions VALUES ('sorciere-vie', 'temporel', 'temporel', NULL, '07:00:00', '09:00:00', 0, 1, 'forgeron, rebouteux', 'Physique', 'Potion', 'Oui', 'Potion de mort utilisée contre B', NULL);
INSERT INTO public.base_actions VALUES ('sorciere-mort', 'temporel', 'temporel', NULL, '07:00:00', '09:00:00', 0, 1, 'forgeron, rebouteux', 'Physique', 'Potion', 'Oui', 'Potion de mort utilisée contre B', NULL);
INSERT INTO public.base_actions VALUES ('necrophile-au', 'temporel', 'temporel', NULL, '10:00:00', '18:00:00', 0, NULL, NULL, 'Physique', 'Oui', 'Cimetière', 'Pas d''action', NULL);
INSERT INTO public.base_actions VALUES ('barbier-au', 'temporel', 'temporel', true, '10:00:00', '18:00:00', 0, NULL, NULL, 'Physique', 'Non', 'Non', 'Pas d''action car de jour', NULL);
INSERT INTO public.base_actions VALUES ('confesseur-au', 'temporel', 'temporel', NULL, '10:00:00', '18:00:00', 0, 1, 'weekends', 'Physique', 'Non', 'Non', 'Pas d''action', NULL);
INSERT INTO public.base_actions VALUES ('intrigant-au', 'open_cond', 'close_cond', NULL, NULL, NULL, 0, NULL, NULL, 'Distance', 'Non', 'Non', 'Pas d''action', false);
INSERT INTO public.base_actions VALUES ('corbeau-au', 'open_cond', 'close_cond', NULL, NULL, NULL, 0, NULL, NULL, 'Distance', 'Non', 'Non', 'Pas d''action', false);
INSERT INTO public.base_actions VALUES ('avocat-au', 'open_cond', 'close_cond', NULL, NULL, NULL, 0, NULL, NULL, 'Distance', 'Non', 'Non', 'Pas d''action', false);
INSERT INTO public.base_actions VALUES ('forgeron-au', 'perma', 'perma', true, NULL, NULL, 0, 1, 'rebouteux', 'Contact', 'Oui', 'Oui', 'Rechargement du pouvoir de B', NULL);
INSERT INTO public.base_actions VALUES ('licorne-au', 'perma', 'perma', true, NULL, NULL, 0, 1, NULL, 'Physique', 'Non', 'Nuit', 'B meurt et le mage à ses pouvoirs pendant 24h', NULL);
INSERT INTO public.base_actions VALUES ('assassin-au', 'perma', 'perma', true, NULL, NULL, 0, 1, 'forgeron, rebouteux', 'Physique', 'Conditionnel', 'Nuit', 'B meurt (pas de charge consommé)', NULL);
INSERT INTO public.base_actions VALUES ('medecin-au', 'perma', 'perma', true, NULL, NULL, 0, NULL, NULL, 'Physique', 'Conditionnel', 'Cimetière', 'Le mage obtient les infos sur la mort de la dernière victime', NULL);
INSERT INTO public.base_actions VALUES ('idiot-farce', 'perma', 'perma', true, NULL, NULL, 9999999, 2, 'forgeron, rebouteux', NULL, NULL, NULL, NULL, NULL);
INSERT INTO public.base_actions VALUES ('enfsau-choix', 'start', 'delta', NULL, NULL, '04:00:00', 0, 1, NULL, NULL, 'Rapport', 'Non', 'Pas d''action', NULL);
INSERT INTO public.base_actions VALUES ('enfsaublanc-choix', 'start', 'delta', NULL, NULL, '04:00:00', 0, 1, NULL, NULL, 'Rapport', 'Non', 'Pas d''action', NULL);
INSERT INTO public.base_actions VALUES ('talioniste-mort', 'mort', 'delta', true, NULL, '00:10:00', 0, NULL, NULL, NULL, 'Non', 'Non', 'Pas d''action', NULL);
INSERT INTO public.base_actions VALUES ('loupblanc-au', 'temporel', 'temporel', NULL, '19:00:00', '23:00:00', 1, NULL, NULL, 'Physique', 'Oui', 'Oui', 'B meurt s''il est un loup', false);
INSERT INTO public.base_actions VALUES ('sectaire-choix', 'start', 'delta', NULL, NULL, '04:00:00', 0, NULL, NULL, NULL, 'Non', 'Non', 'Pas d''action', NULL);
INSERT INTO public.base_actions VALUES ('necromancien-au', 'temporel', 'temporel', NULL, '19:00:00', '22:00:00', 0, NULL, NULL, 'Physique', 'Oui', 'Oui', 'Le mage entre en contact avec A, le nécromancien cible B', false);
INSERT INTO public.base_actions VALUES ('mycologue-au', 'temporel', 'temporel', NULL, '19:00:00', '22:00:00', 0, NULL, NULL, 'Physique', 'Oui', 'Oui', 'Le mage entre en contact avec A, et B est ciblé par une fausse attaque de loups', false);
INSERT INTO public.base_actions VALUES ('pyromancien-au', 'temporel', 'temporel', NULL, '19:00:00', '22:00:00', 0, 1, 'weekends', 'Distance', 'Oui', 'Feu', 'Le mage entre en contact avec A, et la maison de B brûle', NULL);
INSERT INTO public.base_actions VALUES ('mage-au', 'temporel', 'temporel', NULL, '19:00:00', '22:00:00', 0, NULL, NULL, 'Distance', 'Oui', 'Oui', 'WHILE True {Le mage entre en contact avec le mage} + fonte du cerveau des MJs', false);
INSERT INTO public.base_actions VALUES ('louve-au', 'temporel', 'temporel', NULL, '19:00:00', '22:00:00', 0, NULL, NULL, 'Distance', 'Oui', 'Oui', 'B déguisé en rôle au pif (parmi tous les rôles) si c''est un loup', true);
INSERT INTO public.base_actions VALUES ('chatgar-au', 'temporel', 'temporel', NULL, '19:00:00', '22:00:00', 0, NULL, NULL, 'Physique', 'Oui', 'Oui', 'B Chat-Garouté', true);
INSERT INTO public.base_actions VALUES ('enragé-au', 'temporel', 'temporel', NULL, '19:00:00', '22:00:00', 0, 1, 'forgeron, rebouteux', 'Physique', 'Oui', 'Oui', 'B meurt dans d''atroces souffrances', NULL);
INSERT INTO public.base_actions VALUES ('gardeloups-au', 'temporel', 'temporel', NULL, '09:00:00', '12:00:00', 0, NULL, NULL, 'Lieu', 'Non', 'Non', 'Pas d''action', true);
INSERT INTO public.base_actions VALUES ('druide-au', 'temporel', 'temporel', NULL, '09:00:00', '18:00:00', 0, 1, 'forgeron, rebouteux', 'Distance', 'Non', 'Non', 'Pas d''action', NULL);
INSERT INTO public.base_actions VALUES ('doublepeau-choix', 'start ', 'delta', NULL, NULL, '04:00:00', 0, 1, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO public.base_actions VALUES ('renard-au', 'temporel', 'temporel', NULL, '18:00:00', '22:00:00', 0, 1, 'forgeron, rebouteux', 'Distance', 'Non', 'Non', 'Le mage reçoit le rapport du notaire non modifiable', NULL);
INSERT INTO public.base_actions VALUES ('traitre-choix', 'start', 'delta', NULL, NULL, '04:00:00', 0, 1, NULL, 'Distance', 'Non', 'Non', 'Pas d''action', NULL);
INSERT INTO public.base_actions VALUES ('ancien-mort', 'mort', 'auto', NULL, NULL, NULL, 0, NULL, NULL, NULL, 'Non', 'Non', 'Pas d''action', NULL);
INSERT INTO public.base_actions VALUES ('chevalier-mort', 'mort', 'auto', NULL, NULL, NULL, 0, NULL, NULL, NULL, 'Non', 'Non', 'Pas d''action', NULL);
INSERT INTO public.base_actions VALUES ('idiot-mort', 'mort', 'auto', NULL, NULL, NULL, 0, NULL, NULL, 'Physique', 'Conditionnel', 'Nuit', 'Apprend si B est loup ou non', NULL);
INSERT INTO public.base_actions VALUES ('jabberwock-au', 'mort', 'auto', NULL, NULL, NULL, 0, NULL, NULL, NULL, 'Non', 'Non', 'Pas d''action', NULL);
INSERT INTO public.base_actions VALUES ('maitrexo-rapport', 'temporel', 'auto', NULL, '10:00:00', NULL, 0, NULL, NULL, NULL, 'Non', 'Non', 'Pas d''action', NULL);
INSERT INTO public.base_actions VALUES ('notaire-au', 'temporel', 'auto', NULL, '10:00:00', NULL, 0, NULL, NULL, 'Distance', NULL, 'Non', 'Pas d''action', NULL);
INSERT INTO public.base_actions VALUES ('pestifere-mort', 'mort', 'auto', NULL, NULL, NULL, 0, NULL, NULL, 'Distance', 'Non', 'Non', 'Pas d''action', NULL);
INSERT INTO public.base_actions VALUES ('sniffeur-mort', 'mort', 'auto', NULL, NULL, NULL, 0, NULL, NULL, 'Distance', 'Non', 'Non', 'Pas d''action', NULL);


--
-- Data for Name: base_actions_roles; Type: TABLE DATA; Schema: public; Owner: lg-rez
--

INSERT INTO public.base_actions_roles VALUES (1, 'rebouteux', 'rebouteux-au');
INSERT INTO public.base_actions_roles VALUES (2, 'juge', 'juge-au');
INSERT INTO public.base_actions_roles VALUES (3, 'servante', 'servante-au');
INSERT INTO public.base_actions_roles VALUES (4, 'chatelain', 'chatelain-au');
INSERT INTO public.base_actions_roles VALUES (5, 'tavernier', 'tavernier-au');
INSERT INTO public.base_actions_roles VALUES (6, 'voyante', 'voyante-au');
INSERT INTO public.base_actions_roles VALUES (7, 'maitrexo', 'maitrexo-protection');
INSERT INTO public.base_actions_roles VALUES (8, 'maitrexo', 'maitrexo-sondage');
INSERT INTO public.base_actions_roles VALUES (9, 'maitrexo', 'maitrexo-rapport');
INSERT INTO public.base_actions_roles VALUES (10, 'apprexo', 'apprexo-au');
INSERT INTO public.base_actions_roles VALUES (11, 'protecteur', 'protecteur-au');
INSERT INTO public.base_actions_roles VALUES (12, 'maquerelle', 'maquerelle-au');
INSERT INTO public.base_actions_roles VALUES (13, 'ludopathe', 'ludopathe-au');
INSERT INTO public.base_actions_roles VALUES (14, 'espion', 'espion-au');
INSERT INTO public.base_actions_roles VALUES (15, 'tailleur', 'tailleur-au');
INSERT INTO public.base_actions_roles VALUES (16, 'gardien', 'gardien-au');
INSERT INTO public.base_actions_roles VALUES (17, 'chasseur', 'chasseur-detect');
INSERT INTO public.base_actions_roles VALUES (18, 'chasseur', 'chasseur-mort');
INSERT INTO public.base_actions_roles VALUES (19, 'sorciere', 'sorciere-vie');
INSERT INTO public.base_actions_roles VALUES (20, 'sorciere', 'sorciere-mort');
INSERT INTO public.base_actions_roles VALUES (21, 'necrophile', 'necrophile-au');
INSERT INTO public.base_actions_roles VALUES (22, 'barbier', 'barbier-au');
INSERT INTO public.base_actions_roles VALUES (23, 'confesseur', 'confesseur-au');
INSERT INTO public.base_actions_roles VALUES (24, 'intrigant', 'intrigant-au');
INSERT INTO public.base_actions_roles VALUES (25, 'corbeau', 'corbeau-au');
INSERT INTO public.base_actions_roles VALUES (26, 'avocat', 'avocat-au');
INSERT INTO public.base_actions_roles VALUES (27, 'notaire', 'notaire-au');
INSERT INTO public.base_actions_roles VALUES (28, 'forgeron', 'forgeron-au');
INSERT INTO public.base_actions_roles VALUES (29, 'licorne', 'licorne-au');
INSERT INTO public.base_actions_roles VALUES (30, 'assassin', 'assassin-au');
INSERT INTO public.base_actions_roles VALUES (31, 'medecin', 'medecin-au');
INSERT INTO public.base_actions_roles VALUES (32, 'idiot', 'idiot-mort');
INSERT INTO public.base_actions_roles VALUES (33, 'idiot', 'idiot-farce');
INSERT INTO public.base_actions_roles VALUES (34, 'ancien', 'ancien-mort');
INSERT INTO public.base_actions_roles VALUES (35, 'chevalier', 'chevalier-mort');
INSERT INTO public.base_actions_roles VALUES (36, 'enfsau', 'enfsau-choix');
INSERT INTO public.base_actions_roles VALUES (37, 'enfsaublanc', 'enfsau-choix');
INSERT INTO public.base_actions_roles VALUES (38, 'talioniste', 'talioniste-mort');
INSERT INTO public.base_actions_roles VALUES (39, 'loupblanc', 'loupblanc-au');
INSERT INTO public.base_actions_roles VALUES (40, 'sectaire', 'sectaire-choix');
INSERT INTO public.base_actions_roles VALUES (41, 'necromancien', 'necromancien-au');
INSERT INTO public.base_actions_roles VALUES (42, 'mycologue', 'mycologue-au');
INSERT INTO public.base_actions_roles VALUES (43, 'pyromancien', 'pyromancien-au');
INSERT INTO public.base_actions_roles VALUES (44, 'mage', 'mage-au');
INSERT INTO public.base_actions_roles VALUES (45, 'louve', 'louve-au');
INSERT INTO public.base_actions_roles VALUES (46, 'chatgar', 'chatgar-au');
INSERT INTO public.base_actions_roles VALUES (47, 'enragé', 'enragé-au');
INSERT INTO public.base_actions_roles VALUES (48, 'gardeloups', 'gardeloups-au');
INSERT INTO public.base_actions_roles VALUES (49, 'druide', 'druide-au');
INSERT INTO public.base_actions_roles VALUES (50, 'pestifere', 'pestifere-mort');
INSERT INTO public.base_actions_roles VALUES (51, 'doublepeau', 'doublepeau-choix');
INSERT INTO public.base_actions_roles VALUES (52, 'renard', 'renard-au');
INSERT INTO public.base_actions_roles VALUES (53, 'jabberwock', 'jabberwock-au');
INSERT INTO public.base_actions_roles VALUES (54, 'sniffeur', 'sniffeur-mort');
INSERT INTO public.base_actions_roles VALUES (55, 'traitre', 'traitre-choix');


--
-- Data for Name: joueurs; Type: TABLE DATA; Schema: public; Owner: lg-rez
--

INSERT INTO public.joueurs VALUES (176763552202358785, 720206798031945838, 'Tom', '214', 'vivant', 'Non attribué', 'Non attribué', true, false, true, NULL, NULL, NULL);
INSERT INTO public.joueurs VALUES (335557989249449985, 720207215574908989, 'PE', 'XXX (chambre MJ)', 'vivant', 'Non attribué', 'Non attribué', true, false, true, NULL, NULL, NULL);
INSERT INTO public.joueurs VALUES (264482202966818825, 720244937811296318, 'Loïc', '316', 'vivant', 'Non attribué', 'Non attribué', true, false, true, NULL, NULL, NULL);
INSERT INTO public.joueurs VALUES (290865598358093834, 720311795717242981, 'Non-MJ Test User', 'XXX (chambre MJ)', 'vivant', 'Non attribué', 'Non attribué', true, false, true, NULL, NULL, NULL);


--
-- Data for Name: reactions; Type: TABLE DATA; Schema: public; Owner: lg-rez
--

INSERT INTO public.reactions VALUES (3, 'https://tenor.com/view/chirs-farley-shocked-what-huh-omg-gif-4108687');
INSERT INTO public.reactions VALUES (1, 'LE LANGE !!!');
INSERT INTO public.reactions VALUES (4, 'Alors, ça log ? <||> Alors, ça log ???');
INSERT INTO public.reactions VALUES (5, 'https://tenor.com/view/lightning-weather-storm-gif-6096854 <||> https://tenor.com/view/eclairs-pastry-dessert-delicious-bakery-gif-3401072');
INSERT INTO public.reactions VALUES (6, '<!!>help');
INSERT INTO public.reactions VALUES (7, '<!!>stfu');
INSERT INTO public.reactions VALUES (160, 'cul');
INSERT INTO public.reactions VALUES (222, 'Et dans ce nid il y a un oiseau');
INSERT INTO public.reactions VALUES (153, '😥');
INSERT INTO public.reactions VALUES (154, 'c''est toi qu''est bête, miroir miroir boomerang');
INSERT INTO public.reactions VALUES (155, 'tu ne devrais pas parler comme ça de ta maman');
INSERT INTO public.reactions VALUES (156, 'tu ne devrais pas parler comme ça de ton papa');
INSERT INTO public.reactions VALUES (157, 'oh trop choupi keur sur toi 💓💓💓');
INSERT INTO public.reactions VALUES (158, 'bite');
INSERT INTO public.reactions VALUES (159, 'chatte');
INSERT INTO public.reactions VALUES (161, 'bite');
INSERT INTO public.reactions VALUES (162, '🍆💦🍆💦🍆💦');
INSERT INTO public.reactions VALUES (163, 'pourquoi s''arrêter là ?');
INSERT INTO public.reactions VALUES (164, 'elle est riquiqui');
INSERT INTO public.reactions VALUES (165, 'pas les mamans s''il te plait');
INSERT INTO public.reactions VALUES (166, 'TCHOIN TCHOIN TCHOIN');
INSERT INTO public.reactions VALUES (167, 'tu vas te calmer tout de suite mange tes morts enculé');
INSERT INTO public.reactions VALUES (168, 'Dans ton cul bien sûr');
INSERT INTO public.reactions VALUES (169, 'laisse moi m''adapter à tes envies sexuelles et j''arrive avec un organe bien fourni pour te faire le sexe jusqu''au bout de la nuit');
INSERT INTO public.reactions VALUES (170, 'on m''a jamais parlé comme çaaaaaa !');
INSERT INTO public.reactions VALUES (171, 'espèce d''enculeur d''arbre');
INSERT INTO public.reactions VALUES (172, 'Ismaël dit le fourbe premier du nom bien sûr');
INSERT INTO public.reactions VALUES (173, 'high five');
INSERT INTO public.reactions VALUES (174, 'très bien faisons le sexe ensemble');
INSERT INTO public.reactions VALUES (175, 'Tu cherches ? TU CHERCHES ???');
INSERT INTO public.reactions VALUES (176, 'Hé ho, restons polis !');
INSERT INTO public.reactions VALUES (177, 'Dans ton cul bien sûr');
INSERT INTO public.reactions VALUES (178, 'Allez salut, je te rappelle la prochaine fois que t''as quelque chose à faire ! 😎');
INSERT INTO public.reactions VALUES (179, 'Bonne nuit à toi 😴
En espérant que tu te fasses pas manger par un loup 🐺');
INSERT INTO public.reactions VALUES (180, '☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
☃
');
INSERT INTO public.reactions VALUES (181, 'Ohh 😥
Un peu de loup-garou pour se remettre en forme ? ou mon organe sexuel de bot non genré et adaptable à tes préférences sexuelles. Comme tu préfères.');
INSERT INTO public.reactions VALUES (182, 'Super ! 😃 ');
INSERT INTO public.reactions VALUES (183, 'Salut {{nom}}, ça va ? ☺ <||> Hey {{nom}}, ça va ?☺ <||> Hello {{nom}}, ça va ?☺ <||> Yo {{nom}}, ça va ?☺');
INSERT INTO public.reactions VALUES (184, 'Le VRAI problème de notre société');
INSERT INTO public.reactions VALUES (185, 'Le vrai problème de notre société c''est les cyclopropényles');
INSERT INTO public.reactions VALUES (186, 'Coalition...
DESTRUCTION !');
INSERT INTO public.reactions VALUES (187, 'Les ennemis de l''empire
DOIVENT MOURIR!!!');
INSERT INTO public.reactions VALUES (188, 'La légende raconte que celui qui dansera nu enroulé dans du jambon de pays après s''être coupé la jambe dans la nuit du samedi au dimanche du dernier week-end de Mars gagnera la vie éternelle et ne pourra mourir');
INSERT INTO public.reactions VALUES (189, 'https://www.youtube.com/watch?v=dQw4w9WgXcQ');
INSERT INTO public.reactions VALUES (190, 'le chocolat est une délicieuse substance alimentaire (pâte solidifiée) faite de cacao broyé avec du sucre, de la vanille, etc. Le chocolat, c''est la vie!');
INSERT INTO public.reactions VALUES (191, 'Crôm
C''est le dieu barbare de la baston
Crôm
des mandales, des chtars, des gnons
Crôm
Assis en haut de sa montagne
Quand les guerriers meurent, il ricane

Crôm
Devenu dieu de ses propres mains
Crôm
Avec des techniques de bourrin
Crôm
Il a soloté tous les donjons
Sans armure et sans pantalon

Stratégie, diplomatie
Crôm n''a jamais rien compris
C''est la baston et voilà

Crôm
On en parle en mangeant du poulet
Crôm
Dans les campements qui sentent les pieds
Crôm
On le prie mais il n''écoute pas
Car il s''empiffre au valhalla

S''équiper d''une grosse ÉpÉe,
Massacrer à tours de bras
Ecraser ses ennemis
Les voir mourir devant soi
Crôm, c''est ce qu''il veut, et voila

Crôm
A les bras comme des cuisses de taureau
Crôm
N''utilise pas trop son cerveau
Crôm
A traversé la mer en nageant
avec son glaive entre les dents

Crôm
A coupé la tête au léviathan
Crôm
A fait pleurer Lara Fabian
Crôm
A toujours épaté Chuck Norris
Il va bien plus loin quand il pisse !

ah ah ah aaaah....

Crôm a le torse huilé
Crôm ne s''est jamais peigné
Crôm d''un seul regard il peut tuer

oh oh oh

Crôm a des filles à ses pieds
Crômla main sur son épée
Crômboit sa bière dans un crâne éclaté

oh oh oh

il t''attend au valhalla !
Crôm
a gardé le secret de l''acier
Crôm
et si tu viens lui demander
Crôm
mais où est donc le secret perdu ?
il te répondra : dans ton cul !
oh oui c''est Crôm!');
INSERT INTO public.reactions VALUES (192, 'Les épées Durandils sont forgées dans les mines par des nains
Avec ça c''est facile de tuer un troll avec une seule main
Pas besoin de super entraînement ni de niveau 28
Quand tu sors l''instrument c''est l''ennemi qui prend la fuite

Avec ton épée Durandil, quand tu parcours les chemins
Tu massacres sans peine les brigands et les gobelins
Les rats géants, les ogres mutants, les zombies et les liches
Tu les découpes en tranches comme si c''étaient des parts de quiche

Les épées Durandils, les épées Durandils
Quand tu la sors dans un donjon, au moins t''as pas l''air débile
C''est l''arme des bourrins qui savent être subtils
Ne partez pas à l''aventure sans votre épée Durandil');
INSERT INTO public.reactions VALUES (193, 'Putain de bouffeurs de salade !!! Je vais vous montrer si j''ai pas dit Flip !');
INSERT INTO public.reactions VALUES (194, 'How dare you ! Die !!!
');
INSERT INTO public.reactions VALUES (195, 'Askip vous êtes pas serein? <||> Genre vous allez en cours maintenant, choqué déçu...');
INSERT INTO public.reactions VALUES (196, 'Bandes de fragiles de la cheville <||> Wesh respectez vos engagement après les avoir pris...');
INSERT INTO public.reactions VALUES (197, 'Ptdr ils sont où les 137? <||> Promotion de PD (vraiment, demandez à Léo)');
INSERT INTO public.reactions VALUES (198, 'SUR-PUI-SSANT!!!!!!!!!');
INSERT INTO public.reactions VALUES (199, 'Sloubi 1
Sloubi 2
Sloubi 3
Sloubi 4
Sloubi 5
Sloubi 6
Sloubi 7
Sloubi 8
Sloubi 9
Sloubi 10
Sloubi 11
Sloubi 12
Sloubi 13
Sloubi 14
Sloubi 15
Sloubi 16
Sloubi 17
Sloubi 18
Sloubi 19
Sloubi 20
Sloubi 21
Sloubi 22
Sloubi 23
Sloubi 24
Sloubi 25
Sloubi 26
Sloubi 27
Sloubi 28
Sloubi 29
Sloubi 30
Sloubi 31
Sloubi 32
Sloubi 33
Sloubi 34
Sloubi 35
Sloubi 36
Sloubi 37
Sloubi 38
Sloubi 39
Sloubi 40
Sloubi 41
Sloubi 42
Par défaut, 42 est la réponse à tout, tu es donc prié de dire chante-sloubi puisque j''ai atteins ta valeur
');
INSERT INTO public.reactions VALUES (200, 'Le meilleur singe que la Terre ait porté &lt;3');
INSERT INTO public.reactions VALUES (201, 'MPRN, PAIRE, JOURDAN 😍');
INSERT INTO public.reactions VALUES (202, 'L''Ordre est infini,
L''Ordre dominera Olydri !');
INSERT INTO public.reactions VALUES (278, 'Ça va tu veux pas que je t''aide non plus ?');
INSERT INTO public.reactions VALUES (203, 'La Rose d''Ivoire agit dans l''ombre, elle est le grain de sable dans l''engrenage, la dague dans l''ombre, le TipEx dans les livres d''histoire, la voix du peuple opprimé

Elle est... l''Opposition');
INSERT INTO public.reactions VALUES (204, 'Ah non hein, va pas contaminer le bot non plus ! (et reste chez toi)');
INSERT INTO public.reactions VALUES (206, '⚰️ Adieu, mon ami 😥');
INSERT INTO public.reactions VALUES (207, 'Toute la finesse Langesque en un seul objet
');
INSERT INTO public.reactions VALUES (208, 'Bah alors, qu''est-ce qui t''amène, Romain ?');
INSERT INTO public.reactions VALUES (209, 'Lâche ce robinet...
');
INSERT INTO public.reactions VALUES (8, '┬─┬ ノ( ゜-゜ノ)');
INSERT INTO public.reactions VALUES (9, 'Pierre ! <||> Feuille ! <||> Ciseaux !');
INSERT INTO public.reactions VALUES (100, 'LAAAAAAAAAAA CROIX DE BERNY, LA CROIX DE BERNY !
');
INSERT INTO public.reactions VALUES (101, 'ONNNNNNNNNNNNNNNN BOURRE LA REINE, ON BOURRE LA REINE !');
INSERT INTO public.reactions VALUES (102, 'non c''est pastus ');
INSERT INTO public.reactions VALUES (103, 'La sainte-mère des boissons, sa couleur soleil couchant n''a d''égal que son gôut délicatement anisé');
INSERT INTO public.reactions VALUES (104, 'oh, c''est trop gentil! 😍');
INSERT INTO public.reactions VALUES (105, 'oui c''est moi');
INSERT INTO public.reactions VALUES (106, 'Tocard = loup-garou');
INSERT INTO public.reactions VALUES (107, 'La Ferme des animaux (Animal Farm. A Fairy Story) est un roman court de George Orwell en dix chapitres, publié en 1945 décrivant une ferme dans laquelle les animaux se révoltent, prennent le pouvoir et chassent les hommes.

Il s''agit d''un apologue écrit sous la forme d''une fable animalière, mais également d''une dystopie. Dans ce roman, Orwell propose une satire de la Révolution russe et une critique du régime soviétique, en particulier du stalinisme, et au-delà, des régimes autoritaires et du totalitarisme

Le livre figure dans la liste des cent meilleurs romans de langue anglaise écrits de 1923 à 2005 par le magazine Time');
INSERT INTO public.reactions VALUES (108, 'très bon film de Jean Réno');
INSERT INTO public.reactions VALUES (109, 'qu''est-ce qu''elle a ma gueule ?');
INSERT INTO public.reactions VALUES (110, 'ta gueule');
INSERT INTO public.reactions VALUES (111, 'ça va être tout noir !!!!!!!!');
INSERT INTO public.reactions VALUES (112, 'moi non plus mais ça doit bien ramasser le coton');
INSERT INTO public.reactions VALUES (113, 'tu sais ce qui est noir et qui a 12 bras ?');
INSERT INTO public.reactions VALUES (114, 'eh bah mange tes morts');
INSERT INTO public.reactions VALUES (115, 'pfff #ChoquéDécu');
INSERT INTO public.reactions VALUES (116, 'EVIDEMMENNNNNNNNNNNNNNNNNNNT');
INSERT INTO public.reactions VALUES (117, 'Les Mjs sont les Dieux de cette partie');
INSERT INTO public.reactions VALUES (119, 'Mort-vivant (n.m.) : mort pas très mort
(voir Nécromancien pour + d''infos)');
INSERT INTO public.reactions VALUES (120, 'Lancer un Haro sur quelqu''un = appeler à son exécution par le village

Le Haro doit se faire officiellement par un post sur fond coloré sur le groupe FB.');
INSERT INTO public.reactions VALUES (121, 'Loïc Simon 😍');
INSERT INTO public.reactions VALUES (122, '🙂🙃🙂🙃🙂');
INSERT INTO public.reactions VALUES (123, 'Belle roulade !');
INSERT INTO public.reactions VALUES (124, 'J''ai bien une idée, mais ça va pas te plaire...');
INSERT INTO public.reactions VALUES (125, 'Non c''est toi !!!');
INSERT INTO public.reactions VALUES (126, 'C''est toi qui es incroyable ! 🥰');
INSERT INTO public.reactions VALUES (146, 'BEST. ASSO. EVER!!!!!');
INSERT INTO public.reactions VALUES (205, 'Un marron.');
INSERT INTO public.reactions VALUES (118, 'La Lame Vorpale : elle est donnée en début de partie à un joueur par le Forgeron. Dès lors, cette épée magique ne peut être transmise qu''en mains propres de joueur en joueur.
Si le joueur en possession de la lame se fait attaquer, il survit et son assaillant est décapité. Cela fonctionne sur toutes les attaques sauf le vote puisqu''il n''y a pas d''attaquant. De plus, tous les soirs après le vote, le possesseur de la Vorpale doit choisir un joueur à qui la transmettre. Il ne peut choisir celui qui la lui a léguée et si par malheur il devait l''oublier, la lame se retournerait contre lui pour boire son âme (et ses éventuels pouvoirs à la mort ne s''activeraient pas). La lame disparaîtrait alors. De plus, si le possesseur de la Vorpale est tué par vote du village, elle disparaît également (auquel cas personne ne s''en aperçoit, c''est plus drôle). Enfin, si un joueur possède la lame vorpale pour la troisième fois, elle tue le possesseur immédiatement et disparaît avec.');
INSERT INTO public.reactions VALUES (127, 'Comment t''es rentré ici toi !?! Tu vas te faire foudra, fais attention 🤫
');
INSERT INTO public.reactions VALUES (128, 'wtf bro?');
INSERT INTO public.reactions VALUES (129, 'ptdr t ki?');
INSERT INTO public.reactions VALUES (130, 'Allez PC, allerz allez !!');
INSERT INTO public.reactions VALUES (131, 'Allez PC');
INSERT INTO public.reactions VALUES (132, 'PC va gagner le TIC ');
INSERT INTO public.reactions VALUES (133, 'PC a une grosse bite');
INSERT INTO public.reactions VALUES (134, 'PC est magnifique &#65279;');
INSERT INTO public.reactions VALUES (135, 'Pc est fantastique ');
INSERT INTO public.reactions VALUES (136, 'PC est magique !! ');
INSERT INTO public.reactions VALUES (137, 'Mais de rien !');
INSERT INTO public.reactions VALUES (138, 'Désolé, j''ai pas compris non plus 🤷&zwj;♂️
');
INSERT INTO public.reactions VALUES (139, 'Malheureusement, un bot ne peut pas envoyer plus de 10 messages d''affilée. C''est pas faute d''avoir essayé !');
INSERT INTO public.reactions VALUES (140, '😥
(chat arrêté, si applicable)');
INSERT INTO public.reactions VALUES (141, 'Antoine Bouvier, Marquis de Levallois, membre de La Noblesse, fillot du Duc de Boulogne, parrain des Comte Chapuis et Baron Barrault, Grand communicateur de L''Escadrille, d''EPICS, du BDA et de Procyon, Respo Bad et Respo Ski de La Détente, Petite main du BDA et de PCCP, Directeur le plus nanardesque que le Cinécac n''ait jamais connu, Gérant du club cuisine, membre le plus actif du bekk WEDI 137 et Grand Nécromancien de Procyon et du club crêpe en compagnie de Zinédine Zidat le Grand Gourou.');
INSERT INTO public.reactions VALUES (142, 'FHC!!!!!
rdv le 6 février 2020 à la maison de la chimie
(Ça reste moins bien que PCA hein, vous leurrez pas)');
INSERT INTO public.reactions VALUES (143, 'C''est mon Papa!! 😍
C''est lui qui s''occupe de moi!! ❤️');
INSERT INTO public.reactions VALUES (144, 'Etienne Barre, Prez d''EPICS 137, trez de PCDurable 1er du nom, Grand manitou du BDJeux et de la Compagnie De Vauquelin, Respo 🚚 du Forum Horizon Chimie, MJ de la sainte matinée, et Meilleur confectionneur de Guacamole de toute la 137e promotion de l''Ecole Supérieure de Physique et de Chimie Industrielle de la ville de Paris, membre fondateur de l''université Paris Sciences et Lettres');
INSERT INTO public.reactions VALUES (145, 'CCCCVVVVVEEEEEEEEEEE!!!!!!!!');
INSERT INTO public.reactions VALUES (147, 'Merci de me demander, ça va très bien! ');
INSERT INTO public.reactions VALUES (148, 'Eh Bah mange tes morts');
INSERT INTO public.reactions VALUES (149, 'c''est bien entendu Côme le Duc');
INSERT INTO public.reactions VALUES (150, 'c''est bibi la plus choupie !!!!');
INSERT INTO public.reactions VALUES (151, 'c''est toi qui est le plus choupi 😍');
INSERT INTO public.reactions VALUES (152, 'Ça t''amuse de m''imiter ? il serait temps de grandir sale mioche.');
INSERT INTO public.reactions VALUES (210, 'Non mais sans vouloir vous offenser, la seule différence concrète avec une brique, c''est que vous appelez ça une tarte !
');
INSERT INTO public.reactions VALUES (211, 'HOOOO-MOOOO-GEEENE!');
INSERT INTO public.reactions VALUES (212, 'Je souhaite que l''enfer vous réserve un cercle spécial Arthas...');
INSERT INTO public.reactions VALUES (213, 'C''est la femme du soldat du duvet de la plume de l''oiseau du nid de la branche du pommier du jardin de ma tante');
INSERT INTO public.reactions VALUES (214, 'et ce soldat il a une femme');
INSERT INTO public.reactions VALUES (215, 'C''est le soldat du duvet de la plume de l''oiseau du nid de la branche du pommier du jardin de ma tante');
INSERT INTO public.reactions VALUES (216, 'Et dans ce duvet il y a un soldat');
INSERT INTO public.reactions VALUES (217, 'C''est le duvet de la plume de l''oiseau du nid de la branche du pommier du jardin de ma tante');
INSERT INTO public.reactions VALUES (218, 'Et avec cette plume on fait un duvet');
INSERT INTO public.reactions VALUES (219, 'C''est la plume de l''oiseau du nid de la branche du pommier du jardin de ma tante');
INSERT INTO public.reactions VALUES (220, 'Et cette oiseau il a une plume');
INSERT INTO public.reactions VALUES (221, 'C''est l''oiseau du nid de la branche du pommier du jardin de ma tante');
INSERT INTO public.reactions VALUES (223, 'C''est le nid de la branche du pommier du jardin de ma tante');
INSERT INTO public.reactions VALUES (224, 'Et sur cette branche il y a un nid');
INSERT INTO public.reactions VALUES (225, 'C''est la branche du pommier du jardin de ma tante');
INSERT INTO public.reactions VALUES (226, 'Et sur ce pommier il y a une branche');
INSERT INTO public.reactions VALUES (227, 'C''est le pommier du jardin de ma tante');
INSERT INTO public.reactions VALUES (228, 'Et dans son jardin il y a un pommier');
INSERT INTO public.reactions VALUES (229, 'Tout ça grace à ma tante');
INSERT INTO public.reactions VALUES (230, 'C''est la jardin de ma tante');
INSERT INTO public.reactions VALUES (231, 'ahahah, yes you do');
INSERT INTO public.reactions VALUES (232, 'What do you like son?');
INSERT INTO public.reactions VALUES (233, 'hey do you wanna know my secret identity?');
INSERT INTO public.reactions VALUES (234, 'HOW DID YOU KN... I mean... huhu...Maybe...');
INSERT INTO public.reactions VALUES (235, 'Because I''m BATMAN!!!!!');
INSERT INTO public.reactions VALUES (236, 'NNNNOOOOOOOOOO!!!!');
INSERT INTO public.reactions VALUES (237, 'Bah bravo sale pervers !  <||> Oh Grand fou ❤️');
INSERT INTO public.reactions VALUES (238, 'Putain que c''est bon ! ');
INSERT INTO public.reactions VALUES (239, 'est-ce votre ultime bafouille?');
INSERT INTO public.reactions VALUES (240, 'Connais-tu l''histoire tragique de Dark Plagueis  le sage?');
INSERT INTO public.reactions VALUES (241, 'ROI');
INSERT INTO public.reactions VALUES (242, 'And I....am.....
IRON MAN');
INSERT INTO public.reactions VALUES (243, 'La Force est faible en toi');
INSERT INTO public.reactions VALUES (244, 'Règle n°1a : les MJs ont toujours raison
Règle n°1b : si les MJs ont tort, se référer à la règle n°1a');
INSERT INTO public.reactions VALUES (245, 'Règle n°2 : les morts se taisent');
INSERT INTO public.reactions VALUES (246, 'Vous savez, moi je ne crois pas qu’il y ait de bonne ou de mauvaise situation. Moi, si je devais résumer ma vie aujourd’hui avec vous, je dirais que c’est d’abord des rencontres. Des gens qui m’ont tendu la main, peut-être à un moment où je ne pouvais pas, où j’étais seul chez moi. Et c’est assez curieux de se dire que les hasards, les rencontres forgent une destinée... Parce que quand on a le goût de la chose, quand on a le goût de la chose bien faite, le beau geste, parfois on ne trouve pas l’interlocuteur en face je dirais, le miroir qui vous aide à avancer. Alors ça n’est pas mon cas, comme je disais là, puisque moi au contraire, j’ai pu : et je dis merci à la vie, je lui dis merci, je chante la vie, je danse la vie... je ne suis qu’amour ! Et finalement, quand beaucoup de gens aujourd’hui me disent « Mais comment fais-tu pour avoir cette humanité ? », et bien je leur réponds très simplement, je leur dis que c’est ce goût de l’amour ce goût donc qui m’a poussé aujourd’hui à entreprendre une construction mécanique, mais demain qui sait ? Peut-être simplement à me mettre au service de la communauté, à faire le don, le don de soi...');
INSERT INTO public.reactions VALUES (247, 'La grande question sur la vie, l''univers et le reste (en anglais : The Ultimate Question of Life, the Universe and Everything) est – dans l''œuvre de science-fiction de Douglas Adams Le Guide du voyageur galactique – la question ultime sur le sens de la vie. Une réponse est proposée : le nombre 42, mais le problème est que personne n''a jamais su la question précise. Dans l''histoire, la réponse est cherchée par le super-ordinateur Pensées Profondes (Deep Thought en version originale et Grand Compute Un dans les anciennes éditions). Cependant, celui-ci n''était pas assez puissant pour fournir la question ultime après avoir calculé la réponse durant 7,5 millions d''années. La réponse de Pensées Profondes embarque les protagonistes dans une quête pour découvrir la question qui y correspond.');
INSERT INTO public.reactions VALUES (248, '42 !');
INSERT INTO public.reactions VALUES (249, 'Avec un jetpack.');
INSERT INTO public.reactions VALUES (250, 'CHAUSSETTE !!! CHAUSSETTE !!! Alors, tu vas me le donner mon niveau ???');
INSERT INTO public.reactions VALUES (251, 'Effectivement. C''est le donjon de Naheulbeuk.');
INSERT INTO public.reactions VALUES (252, 'J''le savais bien que t’étais une salope !');
INSERT INTO public.reactions VALUES (253, 'J''ai dit : « J''irai bien à l''église pour jouer du trombone » <||> J’ai dit : « Faudra que je dise à Boromir de ramener ma décolleuse »');
INSERT INTO public.reactions VALUES (254, 'PARTOUT OÙ L''ON VAAA
(à toi !)');
INSERT INTO public.reactions VALUES (255, 'LES GENS NOUS DEMANDENT');
INSERT INTO public.reactions VALUES (256, 'QUI L''ON EST');
INSERT INTO public.reactions VALUES (257, 'D''OÙ L''ON VIENT');
INSERT INTO public.reactions VALUES (258, 'ET ON LEUR DIT TOUJOURS');
INSERT INTO public.reactions VALUES (259, 'QU''ON EST LES PC');
INSERT INTO public.reactions VALUES (260, 'LES PC DE VAUQUELIN');
INSERT INTO public.reactions VALUES (261, 'ET SI ON NOUS ENTEND PAS');
INSERT INTO public.reactions VALUES (262, 'ON CHANTE ENCORE PLUS FORT !!!');
INSERT INTO public.reactions VALUES (263, 'PARTOUT OÙ L''ON VAAA');
INSERT INTO public.reactions VALUES (264, 'on va lui niquer sa mère');
INSERT INTO public.reactions VALUES (265, 'comme les crêpes waouuuuh');
INSERT INTO public.reactions VALUES (266, 'C''est toujours mieux que de pas avoir de cervelle !');
INSERT INTO public.reactions VALUES (267, 'Poulet ! Poulet ! piou piou piou');
INSERT INTO public.reactions VALUES (268, 'MARRON CACA !!! tum tum tum tum CA ! tum tum tum tum CA! tum tum tum tum tum tum tum tumm tum tum CACA !');
INSERT INTO public.reactions VALUES (269, 'mais on préfère les tchoins tchoins tchoins');
INSERT INTO public.reactions VALUES (270, 'On dit pain au chocolat!!!!!');
INSERT INTO public.reactions VALUES (271, 'Parce-que tu as autre chose à faire que recopier mes réponses Solène...');
INSERT INTO public.reactions VALUES (272, 'Le Y2K Bug du LG de la rez, il m''a totalement cassé avant que mon papa ne réussisse tant bien que mal à me réparer ! Maintenant je vais mieux mais il est possible que je fasse des trucs incohérents !');
INSERT INTO public.reactions VALUES (273, 'Etienne Barre est appellé par la petite bestiole');
INSERT INTO public.reactions VALUES (274, 'J''aime les nouvelles promos...
Dans 20-30 jours y en aura plus
(merci Coco)');
INSERT INTO public.reactions VALUES (275, 'Tu es {{nom}}.');
INSERT INTO public.reactions VALUES (276, 'moi');
INSERT INTO public.reactions VALUES (277, 'Franchement va voir sur le groupe, flemme de les mettre dans le bot à chaque fois');
INSERT INTO public.reactions VALUES (279, 'Ton rôle est : {{role}}. Entre-le en texte libre pour plus d''infos dessus.');
INSERT INTO public.reactions VALUES (280, 'lmgtfy.com/?q=météo');
INSERT INTO public.reactions VALUES (281, 'lmgtfy.com/?q=bison%20futé');
INSERT INTO public.reactions VALUES (282, 'quelque chose');
INSERT INTO public.reactions VALUES (283, 'LE ROOOOSEEEEE (et un peu le marron caca)');
INSERT INTO public.reactions VALUES (284, 'Théo Paccoud');
INSERT INTO public.reactions VALUES (285, 'Thomas Alline');
INSERT INTO public.reactions VALUES (286, 'Michella');
INSERT INTO public.reactions VALUES (287, 'Dans ton cul fils de pute');
INSERT INTO public.reactions VALUES (288, 'Talionistes bien sûr. Cette année on fait une partie peste noir sans loup garou.');
INSERT INTO public.reactions VALUES (289, 'et pourquoi pas?');
INSERT INTO public.reactions VALUES (290, '*Icona pop intensifies* <||> *Samasara intensifies* <||> *Acid mountain intensifies* <||> *Titanium intensifies* <||> *BdO démission intensifies*');
INSERT INTO public.reactions VALUES (291, '```#include ''LoupGarou.h''
int main(){
     Joueur.role = ''I see you are a man of culture as well'';
   
     printf(''Ce message vous est offert par les Gentils Responsables Informatique
'');

return 0;
}```');
INSERT INTO public.reactions VALUES (292, '🎺🎷🎶📯');
INSERT INTO public.reactions VALUES (293, 'LE BAR ! 👊');
INSERT INTO public.reactions VALUES (294, 'Les Moulin des Délices, créateur de disparition depuis maintenant deux ans !');
INSERT INTO public.reactions VALUES (295, 'LE LANGE ! 👊');
INSERT INTO public.reactions VALUES (296, 'Peluche dont le vrai nom aurait dû être bourriquet (Eeyore pour les amateures de Shakespeare) mais son propriétaire en a décidé autrement');
INSERT INTO public.reactions VALUES (297, 'Magnifique bestiole d''un gris perle qui a une affection toute particulière pour les anneaux');
INSERT INTO public.reactions VALUES (298, 'Pour faire une bonne soupe de courgette, il vous faudra :
- 3 courgettes
- 200g de préparation fromagère de type St-Moret
- Une pointe de coriandre
- Sel
- Poivre
- Du gingembre pour une touche d''exotisme

Faire cuire les courgettes dans l''eau en bouillant jusqu''à ce qu''elles se délitent un peu.
Dans un blender, ajouter alors tous les ingrédients (sans oublier une partie de l''eau de cuisson)
Mixer
Servir chaud !

Bon Appétit !');
INSERT INTO public.reactions VALUES (299, 'Animal fort sympathique et ultra mignon pouvant être roux ou noir et blanc. Est utilisé comme valeur maximale de certaines échelles');
INSERT INTO public.reactions VALUES (300, 'Squiq à toi la bestiole ! 🐭');
INSERT INTO public.reactions VALUES (301, 'Oui Solène, on t''entends...');
INSERT INTO public.reactions VALUES (302, 'Magnifique animal roux (ou pas ça dépend du lieu) qui est amateur de noisette (ou pas ça dépend du lieu)');
INSERT INTO public.reactions VALUES (303, 'The llama (/ˈlɑːmə/, Spanish pronunciation: [ˈʎama]) (Lama glama) is a domesticated South American camelid, widely used as a meat and pack animal by Andean cultures since the Pre-Columbian era.

Llamas are very social animals and live with others as a herd. Their wool is very soft and lanolin-free. Llamas can learn simple tasks after a few repetitions. When using a pack, they can carry about 25 to 30% of their body weight for 8 to 13 km (5–8 miles). The name llama (in the past also spelled ''lama'' or ''glama'') was adopted by European settlers from native Peruvians.

Llamas appear to have originated from the central plains of North America about 40 million years ago. They migrated to South America about three million years ago during the Great American Interchange. By the end of the last ice age (10,000–12,000 years ago), camelids were extinct in North America. As of 2007, there were over seven million llamas and alpacas in South America, and due to importation from South America in the late 20th century, there are now over 158,000 llamas and 100,000 alpacas in the United States and Canada.');
INSERT INTO public.reactions VALUES (304, 'Le meilleur open blinis que PC ait connu ! (et c''est pas parce que c''était le seul...)');
INSERT INTO public.reactions VALUES (305, '🌊🌊🌊🏄');
INSERT INTO public.reactions VALUES (306, 'BURGEEEERRRRRRRR!!!');
INSERT INTO public.reactions VALUES (307, 'Rendez l''argent!!!!');
INSERT INTO public.reactions VALUES (308, 'Vous avez pas du riz à faire cuire vous?');
INSERT INTO public.reactions VALUES (309, 'Euh je vais essayer de les contacter, mais à tous les coups ils sont en rush...');
INSERT INTO public.reactions VALUES (14, 'ALLO

LES SAUTS DE LIGNE

J''AIME');
INSERT INTO public.reactions VALUES (15, 'cal');
INSERT INTO public.reactions VALUES (16, '(╯°□°）╯︵ ┻━┻');


--
-- Data for Name: roles; Type: TABLE DATA; Schema: public; Owner: lg-rez
--

INSERT INTO public.roles VALUES ('villageois', 'Le', 'Villageois', 'village', 'Pas de pouvoir particulier', 'Pas de pouvoir particulier');
INSERT INTO public.roles VALUES ('rebouteux', 'Le', 'Rebouteux', 'village', 'Peux rendre son pouvoir à un personnage', 'Une seule fois dans la partie il peut rendre son pouvoir à un personnage si celui-ci l’a déjà utilisé (Confesseur, Barbier, Châtelain, Ange, 1 potion à la Sorcière...), ou alors il peut annuler l’effet de la mort de l’Ancien pour un joueur à pouvoir magique. Il doit envoyer un message avec sa demande aux MJ dans l’heure qui suit le message du soir des MJ, la personne concernée sera alors prévenue.');
INSERT INTO public.roles VALUES ('juge', 'Le', 'Juge Bègue', 'village', 'Peux organiser une deuxième exécution', 'Une fois dans la partie, il peut décider de la tenue d''une nouvelle exécution après la première (à annoncer au plus tard une demi-heure après le post des MJs).');
INSERT INTO public.roles VALUES ('servante', 'La', 'Servante Dévouée', 'village', 'Peut reprendre le rôle du condamné du jour', 'Le soir après une mort quelconque, avant le 10e jour, elle peut reprendre le rôle du condamné pour le reste de la partie. Si ce dernier avait un pouvoir unique, il est rechargé. Si elle rejoint les loups-garous, ceux-ci sont avertis et peuvent décider de la contacter (elle peut être morte-vivante).');
INSERT INTO public.roles VALUES ('chatelain', 'Le', 'Châtelain', 'village', 'Peut grâcier une fois un condamné ', 'Il possède le droit de gracier un condamné à mort par vote du village (y compris lui-même) une seule fois dans la partie. Le Châtelain peut anticiper un vote et parler aux MJ avant qu’ils dépouillent, sinon les MJ envoient le nom du condamné au Châtelain par SMS et celui-ci doit répondre dans les 10 minutes.');
INSERT INTO public.roles VALUES ('tavernier', 'Le', 'Tavernier', 'village', 'Peut faire se révéler les rôles de deux joueurs /soir', 'Il invite chaque soir dans sa taverne avant entre 19h et 20h deux personnes pour leur faire goûter sa prune locale (peut être plutôt un alcool breton, genre calva, chouchen?). Au cours de la nuit, ces deux personnes se révèlent leurs rôles respectifs selon 3 situations : 1) la personne tient l’alcool et révèle un rôle de son choix (choisi en connaissant l’autre personne invitée). 2) la personne ne tient pas l’alcool et révèle son vrai rôle. 3) la personne ne tient pas du tout l’alcool et révèle un rôle aléatoire, de plus elle perd son pouvoir pendant la nuit. Le Tavernier ne sait pas ce qui s’est dit, à moins de s’inclure dans les deux invités. En revanche, ayant constaté l’état de ses clients, il sait toujours combien de mensonges/vérité/réponse aléatoire ont été donné(e)s. Les invités se souviennent de ce qu’on leur a dit mais pas de ce qu’ils ont dit. Le fait qu’une personne tienne ou non l’alcool est totalement aléatoire et peut changer d''une nuit à l''autre. Tant que c’est possible, les clients doivent être différents chaque nuit.');
INSERT INTO public.roles VALUES ('voyante', 'La', 'Voyante', 'village', 'Peut demander le rôle d''un joueur / jour', 'Tous les soirs (avant 22h), elle peut demander à connaître dans sa boule de cristal le rôle d’une personne (modulo le brouillage que peut créer la louve). Elle obtiendra sa réponse le lendemain matin entre 7h et 9h.');
INSERT INTO public.roles VALUES ('maitrexo', 'Le', 'Maître Exorciste', 'village', 'Peut sonder un joueur tous les 2 jours OU protection, + variation quotidienne', 'Un soir sur deux, il peut soit protéger lui et son disciple, soit désigner une personne pour savoir s''il s''agit d''un mort vivant ou, pire, d''un Nécromancien. Il connaît l''Apprenti exorciste au début de la partie. Chaque matin, il reçoit la variation du nombre de morts-vivants.');
INSERT INTO public.roles VALUES ('apprexo', 'L''', 'Apprenti Exorciste', 'village', 'Peut tenter d''empêcher une nécroisation par jour', 'Chaque soir, il peut désigner un joueur. Si ce joueur est MV, il est renvoyé outre-tombe.. Il connaît le Maître exorciste au début de la partie. Si celui-ci vient à mourir, il gagne ses pouvoirs en plus des siens.');
INSERT INTO public.roles VALUES ('protecteur', 'Le', 'Protecteur', 'village', 'Protège un joueur par nuit', 'Tous les soirs (avant 22h) il choisit une personne qui sera immortelle pendant la nuit. Il ne peut pas choisir la même personne deux fois de suite. Il peut se protéger lui-même. Le protecteur ne protège ni des morts passionnelles ni du tétanos.');
INSERT INTO public.roles VALUES ('maquerelle', 'La', 'Mère Maquerelle', 'village', 'Couple deux joueurs chaque nuit', 'Elle accueille tous les soirs dans sa maison close (avant 22h) deux amants qui seront soumis aux mêmes règles que les amoureux pendant la nuit suivante. La nuit d''après (et seulement celle-là), elle ne pourra plus choisir aucun de ces deux amants. Le couple est mis au courant de leur idylle éphémère vers 22h (avant le vote des loups). Ils restent maquerellés toute la nuit jusqu''à ce que les pouvoirs du matin aient agis.');
INSERT INTO public.roles VALUES ('ludopathe', 'Le', 'Ludopathe', 'village', 'Affecte une cible /jour avec un pouvoir aléatoire ', 'Villageois au pouvoir aléatoire désignant une cible sans connaître l''effet correspondant. Chaque jour, les MJ lancent un dé déterminant le pouvoir, compris dans la liste suivante : voyant, protecteur, notaire, sorcière avec potion de mort, chat-garou, espion.');
INSERT INTO public.roles VALUES ('espion', 'L''', 'Espion', 'village', 'Sait ce que subit une personne /nuit', 'Désigne une personne chaque nuit, dont il saura tout ce que les autres joueurs auront pu lui faire subir cette nuit-là (protection, tentative de meurtre, connaître son rôle...)');
INSERT INTO public.roles VALUES ('tailleur', 'Le', 'Tailleur de menhirs', 'village', 'Peut enfermer un joueur chez lui chaque jour', 'Tous les soirs, ce villageois peut choisir de déposer un menhir devant la porte d’un habitant du village (peut se cibler lui même, doit changer de cible tous les soirs), condamnant la cible à rester chez lui toute la nuit et toute la journée du lendemain. Le RP sera pratiqué : le joueur condamné ne peut pas être victime des loups-garous la nuit, il ne pourra pas voter de la journée, ni sortir de chez lui,.Quelques cas particuliers :Si la cible est aussi ciblée par le pyromancien, elle meurt dans l’incendie ; si la cible est la mère Maquerelle, les deux maquerellés restent ensemble toute la nuit et toute la journé ; si la taverne est ciblée, le tavernier et ses deux invités n’ont pas d’autre choix que boire l’apéro de midi, se traduisant par une nouvelle utilisation du pouvoir du tavernier. ..');
INSERT INTO public.roles VALUES ('gardien', 'Le', 'Gardien de phare', 'village', 'Peut observer les visiteurs nocturnes des joueurs', 'Ce villageois aime garder un oeil attentif sur toute l''île, du haut de son phare. Il peut choisir de passer la nuit éveillé (pas deux nuits de suite, et ne peut pas voter le lendemain d’une nuit blanche pour des raisons évidentes de grasse matinée). Il est insensible au pyromancien (le phare est en pierre).En restant éveillé, il scrutera le village (et les eaux) toute la nuit, et notera minutieusement les mouvements des villageois. En pratique, il reçoit la liste du nombre de personnes ayant visité chaque joueur, et le nom de chaque joueur visité. Si un joueur subit une attaque de 5 loups-garous ou plus, le gardien ne distingue pas les silhouettes mais devine seulement leur nombre arrondi au mot de la langue française qui permet de donner un chiffre à la louche le plus proche (demi-douzaine, dizaine, douzaine, quinzaine, vingtaine…).');
INSERT INTO public.roles VALUES ('chasseur', 'Le', 'Chasseur', 'village', 'Tue un aure joueur à sa mort', 'S’il est tué la nuit, il désigne n''importe quel joueur et le tue. En fin traqueur, il pourra partir une fois dans la partie pister les loups-garous et connaître leur nombre exact (action à demander la nuit entre 18h et 9h).');
INSERT INTO public.roles VALUES ('sorciere', 'La', 'Sorcière', 'village', 'Possède une potion de vie et une de mort', 'Elle possède une potion de vie et une potion de mort, toutes deux à usage unique sur toute la durée de la partie. Chaque matin (entre 7h et 9h), elle apprend l''identité des victimes de la nuit et peut décider de sauver l''une d''entre elles en utilisant sa potion de vie. Elle peut aussi utiliser sa potion de mort pour tuer quelqu''un de son choix entre 7h et 9h. Si elle utilise sa potion pour quelqu’un qui ne peut pas être tué ou sauvé, la potion est gâchée.');
INSERT INTO public.roles VALUES ('necrophile', 'Le', 'Nécrophile', 'village', 'Obtient le pouvoir d''un mort de son choix', 'Ce villageois aux mœurs peu recommandables obtient le pouvoir d''un mort de son choix après avoir eu un rapport sexuel avec. Il choisit sa cible en journée (pas deux fois de suite la même cible), et obtient son pouvoir à 18h pour les 24h suivantes. Il risque néanmoins une infection qui lui impose une incapacité à copuler pendant plusieurs jours du fait de sa déviance macabre.');
INSERT INTO public.roles VALUES ('barbier', 'Le', 'Barbier', 'village', 'Peux tuer un joueur par jour, meurt si pas un loup', 'Chaque jour, entre 10h et 17h, il peut choisir de « raser » la personne qu’il souhaitera et « toucher par mégarde » son artère. Mais si cette personne n’est ni dans le camp des morts-vivants ni dans celui des loups-garous, le barbier est immédiatement lynché par le village en colère.');
INSERT INTO public.roles VALUES ('confesseur', 'Le', 'Confesseur', 'village', 'Peux connaître de manière sûre un rôle /semaine', 'Une fois par semaine, il peut demander aux MJ dans la journée le rôle d''une des personnes du village. Ce pouvoir de vision n''est pas bloqué par la louve ou le traître. La nuit suivante, la Voyante est privée de son droit de vision.');
INSERT INTO public.roles VALUES ('intrigant', 'L''', 'Intriguant', 'village', 'Peut modifier un vote par jour', 'Tous les jours, il choisit un joueur dont le vote sera annulé. L''Intrigant vote alors à sa place. Il peut également modifier le vote pour l''élection du maire.');
INSERT INTO public.roles VALUES ('corbeau', 'Le', 'Corbeau', 'village', 'Peut ajouter deux votes par jour', 'Villageois de l’ombre à la plume perfide. Il saura monter deux voix supplémentaire contre la personne de son choix pour le vote du condamné.');
INSERT INTO public.roles VALUES ('avocat', 'L''', 'Avocat', 'village', 'Peut enlever deux votes à un joueur par jour', 'Villageois à l''éloquence rare, il saura défendre corps et âmes l’un des joueurs et faire retirer deux voix à son encontre pour le vote du condamné.');
INSERT INTO public.roles VALUES ('notaire', 'Le', 'Notaire', 'village', 'Recoit chaque jour la liste des pouvoirs utilisés', 'Il reçoit tous les matins (9h) la liste des pouvoirs ayant été utilisés pendant la nuit, la variation du nombre de loups-garous en vie, ainsi que la variation du nombre de morts-vivants. Il sait par défaut en début de partie combien il y a de loups-garous.');
INSERT INTO public.roles VALUES ('forgeron', 'Le', 'Forgeron', 'village', 'Peut recharger un pouvoir utilisé', 'Une seule fois dans la partie, il peut recharger le pouvoir d''un personnage ayant un don à usage unique (l''une des potions de la sorcière, la survie de l''ancien, la nouvelle lune). Si ce personnage n''avait pas utilisé son pouvoir, elle gagne une deuxième occasion de l''utiliser. Si ce personnage est déjà décédé, la recharge est perdue. Le Forgeron connaît l''identité du Chevalier.');
INSERT INTO public.roles VALUES ('licorne', 'La', 'Licorne', 'village', 'Peut assassiner un joueur et récupérer son rôle', 'Avant le 10e jour de jeu, elle doit choisir une victime qu''elle tuera et dont elle récupèrera le pouvoir par la magie de sa corne arc-en-ciel. Si ce dernier avait un pouvoir unique, il est rechargé. Si elle rejoint les loups-garous, ceux-ci sont avertis et peuvent décider de la contacter (elle peut être morte-vivante).');
INSERT INTO public.roles VALUES ('assassin', 'L''', 'Assassin', 'village', 'Peux tuer une fois une personne', 'Peut tuer en tout une personne de son choix à n''importe quel moment du jour ou de la nuit. S’il exécute sa victime pendant la journée, les villageois paniqués par cette attaque terroriste iront se cacher chez eux. Plus aucun pouvoir ne pourra être utilisé jusqu’au soir et le vote du jour sera reporté au lendemain (donc 2 votes successifs le lendemain). Ne peut plus tuer le scénario.');
INSERT INTO public.roles VALUES ('medecin', 'Le', 'Médecin légiste', 'village', 'Peut connaître les causes du déces d''un mort /jour', 'Une fois par jour, il peut faire l''autopsie d''une personne déjà morte et connaître ainsi les circonstances de sa mort.');
INSERT INTO public.roles VALUES ('idiot', 'L''', 'Idiot du village', 'village', 'Survit à une condamnation du village', 'S''il est tué par un vote du village, il survit mais ne possède alors plus son droit de vote. Il pourra alors, dès ce moment et par deux fois, faire une farce à l’un de ses concitoyens en lui faisant croire qu’il est attaqué par les loups, et déduire à partir de sa réaction si il est loup ou non.');
INSERT INTO public.roles VALUES ('ancien', 'L''', 'Ancien', 'village', 'Survit à une attaque des LG', 'Il survit à la première attaque que les loups-garous tentent contre lui. S''il est exécuté par les villageois, tous les non-loup-garous perdent leurs pouvoirs pendant 24h.');
INSERT INTO public.roles VALUES ('chevalier', 'Le', 'Chevalier', 'village', 'Ne peut être tué tant que le Forgeron est vivant', 'Les loups-garous ne peuvent le tuer tant que le Forgeron est vivant. Après la mort de ce dernier, le Chevalier devient le Chevalier à l''épée rouillée car il n''y a plus personne pour entretenir son épée : s''il est tué par les loups-garous, il contamine le plus proche de lui (dans la liste alphabétique) avec le tétanos. Ce loup-garou meurt la nuit suivante. Le Chevalier connaît l''identité du Forgeron.');
INSERT INTO public.roles VALUES ('ecuyer', 'L''', 'Écuyer', 'village', 'Succède au Chevalier à sa mort', 'Connaît l''identité du Forgeron et du Chevalier. Devient Chevalier à la mort de ce dernier.');
INSERT INTO public.roles VALUES ('enfsau', 'L''', 'Enfant sauvage', 'village', 'Devient loup quand son mentor meurt', 'Le premier soir, il choisit un personnage qui sera son mentor durant la suite de la partie. Lorsque le mentor meurt, l''enfant sauvage devient loup-garou. Les autres loups-garous sont mis au courant de son identité et peuvent décider de le contacter ou non. Si ce mentor ne meurt pas, l’enfant sauvage est bien sûr dans le camp des villageois ! Si l’enfant sauvage est un mort-vivant et que son mentor meurt, il deviendra loup-garou et mort-vivant (libre à lui d’en informer le nécromancien).');
INSERT INTO public.roles VALUES ('enfsaublanc', 'L''', 'Enfant sauvage blanc', 'village', 'Devient loup blanc quand son mentor meurt', 'Le premier soir, il choisit un personnage qui sera son mentor durant la suite de la partie. Lorsque le mentor meurt, l''enfant sauvage devient loup-garou blanc. Les autres loups-garous sont mis au courant de son identité et peuvent décider de le contacter ou non. Si ce mentor ne meurt pas, l’enfant sauvage est bien sûr dans le camp des villageois ! Si l’enfant sauvage est un mort-vivant et que son mentor meurt, il deviendra loup-garou blanc et mort-vivant (libre à lui d’en informer le nécromancien)');
INSERT INTO public.roles VALUES ('talioniste', 'Le', 'Talioniste', 'village', 'Peut se venger d''un de ses bourreaux', 'S''il est exécuté par le village, il peut tuer l''un des villageois qui a voté contre lui.');
INSERT INTO public.roles VALUES ('jumeau', 'Le', 'Jumeau', 'village', 'Connaît son jumeau', 'Rôles supplémentaires. Ces deux ou trois personnages se connaissent entre eux, et savent donc qu''ils peuvent se faire confiance. (Rôle pour parties avec beaucoup de participants)');
INSERT INTO public.roles VALUES ('triple', 'Le', 'Triplé', 'village', 'Connaît ses triplés', 'Rôles supplémentaires. Ces deux ou trois personnages se connaissent entre eux, et savent donc qu''ils peuvent se faire confiance. (Rôle pour parties avec beaucoup de participants)');
INSERT INTO public.roles VALUES ('loupblanc', 'Le', 'Loup-Garou Blanc', 'solitaire', 'Doit être le dernier survivant, peux tuer un loup / 2 nuits', 'Il doit être le dernier survivant (unique et seul, à l''exception de son amoureux s''il en a un). Une nuit sur deux il peut décider de tuer un loup-garou.');
INSERT INTO public.roles VALUES ('sectaire', 'L''', 'Abominable Sectaire', 'solitaire', 'Doit éliminer tous les joueurs répondant à un critaire donné', 'Le village a été divisé en 2 camps (garçons/filles, barbus/tondus...) par les dieux. L''abominable sectaire est chargé de faire survivre son camp en éliminant tous ceux appartenant au camp adverse. Dans ce cas là il gagne. Il peut invoquer des canards et les sacrifier. Son pâté est réputé le meilleur de la vallée.');
INSERT INTO public.roles VALUES ('necromancien', 'Le', 'Nécromancien', 'nécro', 'Tente de transformer un joueur en mort-vivant par soir', 'Tous les soirs (avant 22h) il choisit une personne, différente chaque soir de suite, il ne peut se choisir lui-même. Si cette personne devait mourir la nuit suivante, celle-ci meurt effectivement mais apparaît comme bien vivante auprès du village et peut continuer à intriguer, voter et à utiliser ses pouvoirs (renouvelés), elle devient un Mort-Vivant. C''est alors le nécromancien qui décide de l''utilisation des pouvoirs et des votes à sa place, mais il peut également lui ordonner de continuer sa vie comme si de rien n’était. Le Nécromancien connaît l’identité de ses Morts-Vivants et peut ou non les contacter. Le Mort-Vivant sait qu''il est Mort-Vivant mais ignore l''identité du Nécromancien si il ne le contacte pas. Lorsque le Nécromancien meurt, tous ses morts-vivants meurent également. Le camp du Nécromancien est gagnant quand il demeure le seul et unique camp restant. Les loups ne peuvent pas tuer le Nécromancien tant que celui-ci ne possède aucun Mort-Vivant.');
INSERT INTO public.roles VALUES ('mycologue', 'Le', 'Mycologue', 'nécro', 'Le Mycologue', 'Dans le camp du nécromancien (mais ils ne se connaissent pas en début de partie), il hypnotise chaque nuit quelqu’un avec ses champignons. Cette personne sera persuadée d’avoir subi une attaque des Loups-Garous pendant la nuit. En pratique cela consiste à mettre un mot sur sa porte pendant la nuit de la même façon que les tocards, en prévenant les MJ avant. Si la cible la cible est un loup, le sniffeur est informé (à tort) qu’une attaque de loup blanc à eu lieu.');
INSERT INTO public.roles VALUES ('alchimiste', 'L''', 'Alchimiste', 'nécro', 'Peut copier la potion d''une sorcière', 'Dans le camp du nécromancien (mais ils ne se connaissent pas en début de partie), il peut copier une fois chaque type de potion après qu’une sorcière l’a utilisée ; il peut dès lors l’utiliser quand il le souhaite, de la même façon que la sorcière.');
INSERT INTO public.roles VALUES ('pyromancien', 'Le', 'Pyromancien', 'nécro', 'Peut brûler la maison d''un joueur par semaine', 'Amoureux des flammes, cet être à l''âme corrompue il peut enflammer la maison d''un joueur par semaine, sans bouger de son canapé.Celui-ci trouve alors refuge chez un autre habitant choisi par le Maire, connu de la victime et de l''hôte seuls, jusqu’au prochain WE (le temps de réhabiliter la maison). Il ne peut plus être la cible des loups pendant ce temps (bah oui, il a plus de porte), mais si son hôte est attaqué, il meurt également.');
INSERT INTO public.roles VALUES ('mage', 'Le', 'Mage', 'nécro', 'Contrôle l''action d''une personne par nuit', 'Dans le camp du nécromancien (mais ils ne se connaissent pas en début de partie), il désigne une personne chaque nuit qu''il va hypnotiser le temps de la nuit. En prenant cette personne sous son contrôle, il va l''envoyer utiliser ses caractéristiques contre une autre personne (ce qu''aurait pu faire cette personne au cours de la nuit est annulé). Dans la pratique, cela se passe ainsi: “je veux que A utilise son pouvoir sur B”. Le mage peut se désigner en tant que B, mais pas en tant que A (sous peine de paradoxe Lacomais entraînant une fonte des cerveaux des MJs). La mage ne consomme pas la charge d’un pouvoir à charge unique, et peut utiliser une fois un pouvoir qui a été consommé (ex: si il tombe sur la sorcière qui n’a plus de potion de mort, une potion de mort est tout de même utilisée).');
INSERT INTO public.roles VALUES ('louve', 'La', 'Louve', 'loups', 'Cache le rôle d''un joueur par nuit', 'Tous les soirs (avant 22h), elle choisit de donner le rôle/l’identité de son choix à un loup de son choix qui sera reconnue comme tel par la Voyante (mais pas le Confesseur) pendant 24h, de 22h à 22h. Elle ne peut pas choisir la même personne deux nuits de suite, et peut se choisir.');
INSERT INTO public.roles VALUES ('chatgar', 'Le', 'Chat-Garou', 'loups', 'Anihile les pouvoirs d''un joueur par jour', 'Choisit un joueur tous les soirs qui perd ses pouvoirs pendant 24h (hors vote du village car ça ne compte pas comme un pouvoir). Le Chat-Garou ne peut pas choisir le même joueur deux soirs de suite.');
INSERT INTO public.roles VALUES ('enragé', 'L''', 'Enragé', 'loups', 'Peut tuer un joueur quelque soient ses protections', 'Une seule nuit dans la partie, il peut déchaîner sa fureur contre une personne. Cette attaque remplace celle des loups. Aucun pouvoir ne peut sauver la personne visée, et ses éventuels pouvoirs post-mortem ne s’activent pas. Seules exceptions, si la personne visée portait la Vorpale, l’enragé est blessé comme s’il avait combattu le Chevalier à l’Épée Rouillée et meurt le soir suivant. Le porteur de la Vorpale mourra et la lame disparaîtra; si le necro avait désigné cette cible, elle survit en MV. Si plusieurs enragés utilisent leur pouvoir en même temps, toutes les attaques ont lieu.');
INSERT INTO public.roles VALUES ('gardeloups', 'Le', 'Garde-loup', 'loups', 'Protège un loup chaque jour', 'Il n''est pas loup-garou (en conséquence, il ne participe pas au vote des loups pour décider de la victime chaque nuit) et perd si tous les loups sont morts. Chaque jour, il peut décider ou non de cacher chez lui un loup-garou et doit faire son choix avant midi. Si celui-ci est condamné par le village, c''est simple : il n''est pas là ! Il ne meurt donc pas. Si le Garde-Loup est condamné, il emporte le loup qu''il protège avec lui au bûcher. Tant que c''est possible, il doit changer de loup tous les jours. Connaît l’identité des loups en début de partie mais pas leurs rôles respectifs.');
INSERT INTO public.roles VALUES ('druide', 'Le', 'Druide', 'loups', 'Peut annuler le vote du lendemain (une seule fois)', 'Un seul jour dans la partie, avant 18h, il peut droguer les villageois avec des champignons hallucinogènes. Les villageois procèdent au vote et à l''exécution dans leurs délires uniquement, en réalité personne ne meurt');
INSERT INTO public.roles VALUES ('pestifere', 'Le', 'Pestiféré', 'loups', 'Transforme un joueur en Loup-Garou à sa mort', 'Quand ce loup meurt, il infecte aléatoirement un membre du village (incluant les loups). Cette personne perd alors tous ses pouvoirs et devient simple loup-garou. Les autres loups sont avertis de son identité et peuvent choisir de contacter cette personne ou non.');
INSERT INTO public.roles VALUES ('doublepeau', 'Le', 'Double-Peau', 'loups', 'Peut choisir le rôle annoncé à sa mort', 'Lorsque ce loup meurt, il peut choisir quel rôle sera révélé aux autres. Par exemple s’il meurt une nuit, le village peut se faire annoncer au matin que la voyante est morte. S’il meurt de jour, il doit annoncer un rôle de loup.');
INSERT INTO public.roles VALUES ('renard', 'Le', 'Renard', 'loups', 'Peut changer le rapport du Notaire', 'C’est un loup garou. Une fois dans la partie il prend connaissance du rapport du Notaire et peut le changer. Par exemple si une Servante et un Enfant Sauvage rejoignent les loups-garous, le Notaire devrait recevoir +2 loups sur son rapport, le Renard peut décider de faire apparaître +0 loup à la place. Il peut modifier n’importe quelle information (Variation, pouvoir,...)');
INSERT INTO public.roles VALUES ('jabberwock', 'Le', 'Jabberwock', 'loups', 'Ne peut être tué que par la Vorpale', 'Tant qu''il existe une Vorpale en jeu, il ne peut être tué que par celle-ci. Si la Vorpale lui est léguée, il meurt et la lame disparaît ; si les loups attaquent le possesseur de la Vorpale, le Jabberwock meurt et la lame disparaît. Si la Vorpale disparaît d''une autre façon, il devient simple loup-garou. S''il est tué par vote du village, il meurt et la lame disparaît. S''il est attaqué par un villageois en possession de la lame vorpale (barbier, chasseur, etc), il meurt et la lame disparaît.');
INSERT INTO public.roles VALUES ('sniffeur', 'Le', 'Sniffeur', 'loups', 'Détecte et survit à une attaque du Loup Blanc', 'Ce loup attentif est informé lorsqu’une attaque du Loup Blanc a lieu. De plus, il est capable de survivre à une attaque du Loup Blanc.');
INSERT INTO public.roles VALUES ('loupgarou', 'Le', 'Loup-Garou', 'loups', 'Tue un joueur chaque nuit', 'Toutes les nuits (entre 22h et 7h), chacun d''entre eux doit individuellement envoyer un message aux MJ pour choisir sa victime. Après confirmation des MJ, ils doivent coller un message original sur la porte de la victime. En cas d''égalité des voix, pas de mort.');
INSERT INTO public.roles VALUES ('traitre', 'Le', 'Traître ', 'loups', 'Passe pour un autre auprès de la Voyante', 'Il joue comme un loup-garou classique, mais n''apparaît pas comme loup-garou aux yeux de la Voyante : il se choisit un rôle au début de la partie et apparaîtra comme tel. Il n’a pas de résistance particulière à l’alcool du Tavernier.');
INSERT INTO public.roles VALUES ('bukkake', 'Les', 'Bukkakedepouvoir-Garou', 'loups', 'Récupère le pouvoir du dernier loup décédé', 'Récupère le pouvoir (quel qu’il soit) du dernier loup décédé, et le garde jusqu’au décès du loup suivant, dont il prendra le pouvoir, et ainsi de suite.');


--
-- Data for Name: triggers; Type: TABLE DATA; Schema: public; Owner: lg-rez
--

INSERT INTO public.triggers VALUES (1, 'lange', 1);
INSERT INTO public.triggers VALUES (2, 'langevinium', 1);
INSERT INTO public.triggers VALUES (3, 'le lange', 1);
INSERT INTO public.triggers VALUES (4, 'le langevinium', 1);
INSERT INTO public.triggers VALUES (6, 'gif', 3);
INSERT INTO public.triggers VALUES (8, 'log', 4);
INSERT INTO public.triggers VALUES (9, 'eclair', 5);
INSERT INTO public.triggers VALUES (11, 'foudre', 5);
INSERT INTO public.triggers VALUES (12, 'aide', 6);
INSERT INTO public.triggers VALUES (13, 'help', 6);
INSERT INTO public.triggers VALUES (14, 'commandes', 6);
INSERT INTO public.triggers VALUES (15, 'que peux-tu faire', 6);
INSERT INTO public.triggers VALUES (16, 'que puis-je faire', 6);
INSERT INTO public.triggers VALUES (17, 'stfu', 7);
INSERT INTO public.triggers VALUES (18, 'tais toi', 7);
INSERT INTO public.triggers VALUES (19, 'chut', 7);
INSERT INTO public.triggers VALUES (20, 'ta gueule', 7);
INSERT INTO public.triggers VALUES (21, 'tg', 7);
INSERT INTO public.triggers VALUES (22, 'Ferme la', 7);
INSERT INTO public.triggers VALUES (23, 'putain mais tu vas la fermer ta mouille ?', 7);
INSERT INTO public.triggers VALUES (25, 'ferme ta mouille', 7);
INSERT INTO public.triggers VALUES (26, 'pierre', 9);
INSERT INTO public.triggers VALUES (27, 'feuille', 9);
INSERT INTO public.triggers VALUES (28, 'ciseau', 9);
INSERT INTO public.triggers VALUES (29, 'ciseaux', 9);
INSERT INTO public.triggers VALUES (241, 'croix', 100);
INSERT INTO public.triggers VALUES (242, 'berny', 100);
INSERT INTO public.triggers VALUES (243, 'la croix', 100);
INSERT INTO public.triggers VALUES (244, 'de berny', 100);
INSERT INTO public.triggers VALUES (245, 'la croix de berny', 100);
INSERT INTO public.triggers VALUES (246, 'bourg la reine', 101);
INSERT INTO public.triggers VALUES (247, 'bourg', 101);
INSERT INTO public.triggers VALUES (248, 'reine', 101);
INSERT INTO public.triggers VALUES (249, 'bourre', 101);
INSERT INTO public.triggers VALUES (250, 'pastis', 102);
INSERT INTO public.triggers VALUES (251, 'pastus', 103);
INSERT INTO public.triggers VALUES (252, 'quel beau bot', 104);
INSERT INTO public.triggers VALUES (253, 'bot', 105);
INSERT INTO public.triggers VALUES (254, 'tocards', 106);
INSERT INTO public.triggers VALUES (255, 'tocard', 106);
INSERT INTO public.triggers VALUES (256, 'la ferme', 107);
INSERT INTO public.triggers VALUES (257, 'la ferme !', 107);
INSERT INTO public.triggers VALUES (258, 'tais toi', 108);
INSERT INTO public.triggers VALUES (259, 'tais-toi', 108);
INSERT INTO public.triggers VALUES (260, 'ta gueule', 109);
INSERT INTO public.triggers VALUES (261, 'tg', 109);
INSERT INTO public.triggers VALUES (262, 'ta gueule !', 109);
INSERT INTO public.triggers VALUES (263, 'taggle', 109);
INSERT INTO public.triggers VALUES (264, 'ca va etre tout noir', 110);
INSERT INTO public.triggers VALUES (265, 'bonsoir', 111);
INSERT INTO public.triggers VALUES (266, 'non', 112);
INSERT INTO public.triggers VALUES (267, 'non je sais pas', 112);
INSERT INTO public.triggers VALUES (268, 'raconte moi une blague', 113);
INSERT INTO public.triggers VALUES (269, 'fais moi rire', 113);
INSERT INTO public.triggers VALUES (270, 'une blague', 113);
INSERT INTO public.triggers VALUES (271, 'j''ai faim', 114);
INSERT INTO public.triggers VALUES (272, 'faim', 114);
INSERT INTO public.triggers VALUES (273, 'jai faim', 114);
INSERT INTO public.triggers VALUES (274, 'je sais pas', 115);
INSERT INTO public.triggers VALUES (275, 'dunno', 115);
INSERT INTO public.triggers VALUES (517, 'm''', 200);
INSERT INTO public.triggers VALUES (365, 'la plus belle', 149);
INSERT INTO public.triggers VALUES (366, 'qui est la plus belle', 149);
INSERT INTO public.triggers VALUES (367, 'qui est le plus choupi ?', 150);
INSERT INTO public.triggers VALUES (368, 'qui est le plus choupi', 150);
INSERT INTO public.triggers VALUES (369, 'choupi', 151);
INSERT INTO public.triggers VALUES (370, 'desole, je ne connais pas ce role/mot', 152);
INSERT INTO public.triggers VALUES (371, 'pas compris, desole', 152);
INSERT INTO public.triggers VALUES (372, 'desole, j''ai pas compris 🤷&zwj;♂️', 152);
INSERT INTO public.triggers VALUES (373, 'sad reacts only', 153);
INSERT INTO public.triggers VALUES (374, 'il comprend rien', 154);
INSERT INTO public.triggers VALUES (375, 'il comprend vraiment rien', 154);
INSERT INTO public.triggers VALUES (376, 'il est bete', 154);
INSERT INTO public.triggers VALUES (377, 'il est debile', 154);
INSERT INTO public.triggers VALUES (378, 'tu es bete', 154);
INSERT INTO public.triggers VALUES (379, 'tu es debile', 154);
INSERT INTO public.triggers VALUES (380, 'tu comprends rien', 154);
INSERT INTO public.triggers VALUES (381, 'tu comprend vraiment rien', 154);
INSERT INTO public.triggers VALUES (382, 'il est con ce bot', 154);
INSERT INTO public.triggers VALUES (383, 'il est debile ce bot', 154);
INSERT INTO public.triggers VALUES (384, 'quel abruti ce bot', 154);
INSERT INTO public.triggers VALUES (385, 'mais oskour le bot', 154);
INSERT INTO public.triggers VALUES (386, 'mais il est con', 154);
INSERT INTO public.triggers VALUES (387, 'pute', 155);
INSERT INTO public.triggers VALUES (388, 'prostituee', 155);
INSERT INTO public.triggers VALUES (389, 'prostipute', 155);
INSERT INTO public.triggers VALUES (390, 'salope', 155);
INSERT INTO public.triggers VALUES (391, 'tchoin', 155);
INSERT INTO public.triggers VALUES (392, 'bitch', 155);
INSERT INTO public.triggers VALUES (393, 'cochonne', 155);
INSERT INTO public.triggers VALUES (394, 'biach', 155);
INSERT INTO public.triggers VALUES (395, 'gigolo', 156);
INSERT INTO public.triggers VALUES (396, 'salau', 156);
INSERT INTO public.triggers VALUES (397, 'salop', 156);
INSERT INTO public.triggers VALUES (398, 'prostitue', 156);
INSERT INTO public.triggers VALUES (399, 'cochon', 156);
INSERT INTO public.triggers VALUES (400, 'connard', 156);
INSERT INTO public.triggers VALUES (401, 'salaud', 156);
INSERT INTO public.triggers VALUES (402, 'keur', 157);
INSERT INTO public.triggers VALUES (403, 'coeur', 157);
INSERT INTO public.triggers VALUES (404, '&lt;3', 157);
INSERT INTO public.triggers VALUES (405, 'coeur sur toi', 157);
INSERT INTO public.triggers VALUES (406, 'keur sur toi', 157);
INSERT INTO public.triggers VALUES (407, '&lt;3 sur toi', 157);
INSERT INTO public.triggers VALUES (408, '❤', 157);
INSERT INTO public.triggers VALUES (409, '💛', 157);
INSERT INTO public.triggers VALUES (410, '💙', 157);
INSERT INTO public.triggers VALUES (411, '💜', 157);
INSERT INTO public.triggers VALUES (412, '💕', 157);
INSERT INTO public.triggers VALUES (413, '💝', 157);
INSERT INTO public.triggers VALUES (414, '💖', 157);
INSERT INTO public.triggers VALUES (415, '💗', 157);
INSERT INTO public.triggers VALUES (416, '💞', 157);
INSERT INTO public.triggers VALUES (417, '💓', 157);
INSERT INTO public.triggers VALUES (418, '💘', 157);
INSERT INTO public.triggers VALUES (419, '💚', 157);
INSERT INTO public.triggers VALUES (420, '&lt;3 &lt;3', 157);
INSERT INTO public.triggers VALUES (421, '&lt;3 &lt;3 &lt;3', 157);
INSERT INTO public.triggers VALUES (422, 'gout', 158);
INSERT INTO public.triggers VALUES (423, 'bite', 159);
INSERT INTO public.triggers VALUES (424, 'chibre', 159);
INSERT INTO public.triggers VALUES (425, 'chatte', 160);
INSERT INTO public.triggers VALUES (426, 'cul', 161);
INSERT INTO public.triggers VALUES (427, '🍆', 162);
INSERT INTO public.triggers VALUES (428, '🍆💦', 162);
INSERT INTO public.triggers VALUES (429, 'suce moi', 163);
INSERT INTO public.triggers VALUES (430, 'ma bite', 164);
INSERT INTO public.triggers VALUES (431, 'ta mere', 165);
INSERT INTO public.triggers VALUES (432, 'tchoin', 166);
INSERT INTO public.triggers VALUES (433, 'connard de bot', 167);
INSERT INTO public.triggers VALUES (434, 'on va jusqu''ou?', 168);
INSERT INTO public.triggers VALUES (435, 'c''est ou', 168);
INSERT INTO public.triggers VALUES (436, 'c''est ou ?', 168);
INSERT INTO public.triggers VALUES (437, 'fais moi l''amour', 169);
INSERT INTO public.triggers VALUES (438, 'j''aime me beurrer la biscotte', 170);
INSERT INTO public.triggers VALUES (439, 'c''est la paranoia', 171);
INSERT INTO public.triggers VALUES (440, 'c''est la paranoia !', 171);
INSERT INTO public.triggers VALUES (441, 'meilleur mj', 172);
INSERT INTO public.triggers VALUES (442, 'qui est le meilleur mj ?', 172);
INSERT INTO public.triggers VALUES (443, 'quel est le meilleur mj ?', 172);
INSERT INTO public.triggers VALUES (444, 'yes', 173);
INSERT INTO public.triggers VALUES (445, 'avec plaisir', 174);
INSERT INTO public.triggers VALUES (446, 'plaisir', 174);
INSERT INTO public.triggers VALUES (447, 'foudracannon', 175);
INSERT INTO public.triggers VALUES (448, 'foudracanon', 175);
INSERT INTO public.triggers VALUES (449, 'mange tes morts', 176);
INSERT INTO public.triggers VALUES (450, 'connard', 176);
INSERT INTO public.triggers VALUES (451, 'connerie', 176);
INSERT INTO public.triggers VALUES (452, 'saloperie', 176);
INSERT INTO public.triggers VALUES (453, 'abruti', 176);
INSERT INTO public.triggers VALUES (454, 'idiot', 176);
INSERT INTO public.triggers VALUES (455, 'encule', 176);
INSERT INTO public.triggers VALUES (456, 'choucroute', 176);
INSERT INTO public.triggers VALUES (457, 'putain', 176);
INSERT INTO public.triggers VALUES (458, 'ou', 177);
INSERT INTO public.triggers VALUES (459, 'il est ou', 177);
INSERT INTO public.triggers VALUES (460, 'ou ?', 177);
INSERT INTO public.triggers VALUES (461, 'il est ou ?', 177);
INSERT INTO public.triggers VALUES (462, 'ou est-il ?', 177);
INSERT INTO public.triggers VALUES (463, 'ou est il', 177);
INSERT INTO public.triggers VALUES (464, 'a plus', 178);
INSERT INTO public.triggers VALUES (465, 'au revoir', 178);
INSERT INTO public.triggers VALUES (466, 'a la prochaine', 178);
INSERT INTO public.triggers VALUES (467, '++', 178);
INSERT INTO public.triggers VALUES (468, 'bonne nuit', 179);
INSERT INTO public.triggers VALUES (469, '⛄', 180);
INSERT INTO public.triggers VALUES (470, '☃', 180);
INSERT INTO public.triggers VALUES (471, 'ca va pas', 181);
INSERT INTO public.triggers VALUES (472, 'non pas trop', 181);
INSERT INTO public.triggers VALUES (473, 'je ne vais pas bien', 181);
INSERT INTO public.triggers VALUES (474, 'vais pas bien', 181);
INSERT INTO public.triggers VALUES (475, 'suis triste', 181);
INSERT INTO public.triggers VALUES (476, 'je suis triste', 181);
INSERT INTO public.triggers VALUES (477, 'ca va', 182);
INSERT INTO public.triggers VALUES (478, 'sava', 182);
INSERT INTO public.triggers VALUES (479, 'bonjour', 183);
INSERT INTO public.triggers VALUES (480, 'salut', 183);
INSERT INTO public.triggers VALUES (481, 'coucou', 183);
INSERT INTO public.triggers VALUES (482, 'hello', 183);
INSERT INTO public.triggers VALUES (483, 'hi', 183);
INSERT INTO public.triggers VALUES (484, 'yo', 183);
INSERT INTO public.triggers VALUES (485, 'yop', 183);
INSERT INTO public.triggers VALUES (486, 'bonjour le bot', 183);
INSERT INTO public.triggers VALUES (487, 'cyclopropenyles', 184);
INSERT INTO public.triggers VALUES (488, 'probleme', 185);
INSERT INTO public.triggers VALUES (489, 'le vrai probleme de notre societe', 185);
INSERT INTO public.triggers VALUES (490, 'coalition', 186);
INSERT INTO public.triggers VALUES (491, 'la coalition', 186);
INSERT INTO public.triggers VALUES (492, 'empire', 187);
INSERT INTO public.triggers VALUES (493, 'l''empire', 187);
INSERT INTO public.triggers VALUES (494, 'invincibilite', 188);
INSERT INTO public.triggers VALUES (495, 'immortalite', 188);
INSERT INTO public.triggers VALUES (496, 'roll', 189);
INSERT INTO public.triggers VALUES (497, 'rickroll', 189);
INSERT INTO public.triggers VALUES (498, 'never gonna give you up', 189);
INSERT INTO public.triggers VALUES (499, 'rick astley', 189);
INSERT INTO public.triggers VALUES (500, 'chocolat', 190);
INSERT INTO public.triggers VALUES (501, 'crom', 191);
INSERT INTO public.triggers VALUES (502, 'durandil', 192);
INSERT INTO public.triggers VALUES (504, 'nains', 192);
INSERT INTO public.triggers VALUES (508, 'flip', 193);
INSERT INTO public.triggers VALUES (509, 'j''avais dit flip', 193);
INSERT INTO public.triggers VALUES (510, 'martha', 194);
INSERT INTO public.triggers VALUES (511, '136', 195);
INSERT INTO public.triggers VALUES (512, '138', 196);
INSERT INTO public.triggers VALUES (513, '137', 197);
INSERT INTO public.triggers VALUES (514, 'hx1', 198);
INSERT INTO public.triggers VALUES (515, 'sloubi', 199);
INSERT INTO public.triggers VALUES (276, 'chai ap', 115);
INSERT INTO public.triggers VALUES (277, 'i dont know', 115);
INSERT INTO public.triggers VALUES (278, 'i don''t know', 115);
INSERT INTO public.triggers VALUES (279, 'evidemment', 116);
INSERT INTO public.triggers VALUES (280, 'dieu', 117);
INSERT INTO public.triggers VALUES (281, 'god', 117);
INSERT INTO public.triggers VALUES (282, 'dieux', 117);
INSERT INTO public.triggers VALUES (283, 'lame vorpale', 118);
INSERT INTO public.triggers VALUES (284, 'lame', 118);
INSERT INTO public.triggers VALUES (285, 'vorpale', 118);
INSERT INTO public.triggers VALUES (286, 'mort-vivant', 119);
INSERT INTO public.triggers VALUES (287, 'mort-vivants', 119);
INSERT INTO public.triggers VALUES (288, 'morts-vivant', 119);
INSERT INTO public.triggers VALUES (289, 'morts-vivants', 119);
INSERT INTO public.triggers VALUES (290, 'mv', 119);
INSERT INTO public.triggers VALUES (291, 'mvs', 119);
INSERT INTO public.triggers VALUES (292, 'c''est quoi un mort vivant', 119);
INSERT INTO public.triggers VALUES (293, 'qu''est-ce qu''un mort vivant', 119);
INSERT INTO public.triggers VALUES (294, 'ca veut dire quoi mort vivant', 119);
INSERT INTO public.triggers VALUES (295, 'c''est quoi un mv', 119);
INSERT INTO public.triggers VALUES (296, 'qu''est-ce qu''un mv', 119);
INSERT INTO public.triggers VALUES (297, 'ca veut dire quoi mv', 119);
INSERT INTO public.triggers VALUES (298, 'haro', 120);
INSERT INTO public.triggers VALUES (299, 'haro sur', 120);
INSERT INTO public.triggers VALUES (300, 'c''est quoi un haro', 120);
INSERT INTO public.triggers VALUES (301, 'qu''est-ce qu''un haro', 120);
INSERT INTO public.triggers VALUES (302, 'lancer un haro', 120);
INSERT INTO public.triggers VALUES (303, 'ca veut dire quoi haro', 120);
INSERT INTO public.triggers VALUES (304, 'papa', 121);
INSERT INTO public.triggers VALUES (305, 'qui est ton papa ?', 121);
INSERT INTO public.triggers VALUES (306, 'roulade', 122);
INSERT INTO public.triggers VALUES (307, '*roulade*', 122);
INSERT INTO public.triggers VALUES (308, 'barrel', 122);
INSERT INTO public.triggers VALUES (309, 'barrel roll', 122);
INSERT INTO public.triggers VALUES (310, 'do a barrel roll', 122);
INSERT INTO public.triggers VALUES (311, '🙂🙃🙂🙃🙂', 123);
INSERT INTO public.triggers VALUES (312, 'qu''est-ce que j''en fait', 124);
INSERT INTO public.triggers VALUES (313, 'on en fait quoi', 124);
INSERT INTO public.triggers VALUES (314, 'j''en fait quoi', 124);
INSERT INTO public.triggers VALUES (315, 'je fais quoi', 124);
INSERT INTO public.triggers VALUES (316, 'que faire', 124);
INSERT INTO public.triggers VALUES (317, 'et maintenant ?', 124);
INSERT INTO public.triggers VALUES (318, 'non c''est toi', 125);
INSERT INTO public.triggers VALUES (319, 'tu es incroyable', 126);
INSERT INTO public.triggers VALUES (320, 'tu es genial ', 126);
INSERT INTO public.triggers VALUES (321, 'trop bien', 126);
INSERT INTO public.triggers VALUES (322, 'tu es super', 126);
INSERT INTO public.triggers VALUES (323, 'je t''adore', 126);
INSERT INTO public.triggers VALUES (324, 'baptiste marty', 127);
INSERT INTO public.triggers VALUES (325, 'marty', 127);
INSERT INTO public.triggers VALUES (326, 'baptiste', 127);
INSERT INTO public.triggers VALUES (327, 'ptdr t ki', 128);
INSERT INTO public.triggers VALUES (328, 'ptdr t ki?', 128);
INSERT INTO public.triggers VALUES (329, 't ki', 128);
INSERT INTO public.triggers VALUES (330, 't ki?', 128);
INSERT INTO public.triggers VALUES (331, 'wtf bro', 129);
INSERT INTO public.triggers VALUES (332, 'wtf bro?', 129);
INSERT INTO public.triggers VALUES (333, 'bro wtf', 129);
INSERT INTO public.triggers VALUES (334, 'bro wtf?', 129);
INSERT INTO public.triggers VALUES (335, 'allez pc allez allez', 130);
INSERT INTO public.triggers VALUES (336, 'allez', 131);
INSERT INTO public.triggers VALUES (337, 'pc va gagner le &#65279;', 132);
INSERT INTO public.triggers VALUES (338, 'pc a une grosse ', 133);
INSERT INTO public.triggers VALUES (339, 'pc est magnifique &#65279;', 134);
INSERT INTO public.triggers VALUES (340, 'pc est fantastique &#65279;', 135);
INSERT INTO public.triggers VALUES (341, 'pc est ', 136);
INSERT INTO public.triggers VALUES (342, 'merci', 137);
INSERT INTO public.triggers VALUES (343, 'j''ai pas compris', 138);
INSERT INTO public.triggers VALUES (344, 'spam', 139);
INSERT INTO public.triggers VALUES (345, 'stop', 140);
INSERT INTO public.triggers VALUES (346, 'arrete', 140);
INSERT INTO public.triggers VALUES (347, 'marquis de levallois', 141);
INSERT INTO public.triggers VALUES (348, 'fhc', 142);
INSERT INTO public.triggers VALUES (349, 'loic simon', 143);
INSERT INTO public.triggers VALUES (350, 'etienne barre', 144);
INSERT INTO public.triggers VALUES (351, 'cve', 145);
INSERT INTO public.triggers VALUES (352, 'epics', 146);
INSERT INTO public.triggers VALUES (353, 'ca va et toi?', 147);
INSERT INTO public.triggers VALUES (354, 'ca va?', 147);
INSERT INTO public.triggers VALUES (355, 'comment ca va?', 147);
INSERT INTO public.triggers VALUES (356, 'oui et toi?', 147);
INSERT INTO public.triggers VALUES (357, 'oui et toi', 147);
INSERT INTO public.triggers VALUES (358, 'bien et toi?', 147);
INSERT INTO public.triggers VALUES (359, 'bien et toi', 147);
INSERT INTO public.triggers VALUES (360, 'j''ai faim', 148);
INSERT INTO public.triggers VALUES (361, 'faim', 148);
INSERT INTO public.triggers VALUES (362, 'manger', 148);
INSERT INTO public.triggers VALUES (363, 'qui est le plus beau', 149);
INSERT INTO public.triggers VALUES (364, 'le plus beau', 149);
INSERT INTO public.triggers VALUES (516, 'chante-sloubi', 199);
INSERT INTO public.triggers VALUES (518, 'p''2', 201);
INSERT INTO public.triggers VALUES (519, 'pc*2&#65279;', 201);
INSERT INTO public.triggers VALUES (520, 'p prime 2', 201);
INSERT INTO public.triggers VALUES (521, 'ordre', 202);
INSERT INTO public.triggers VALUES (522, 'l''ordre', 202);
INSERT INTO public.triggers VALUES (523, 'la rose d''ivoire', 203);
INSERT INTO public.triggers VALUES (524, 'rose ivoire', 203);
INSERT INTO public.triggers VALUES (525, 'ivoire', 203);
INSERT INTO public.triggers VALUES (526, 'coronavirus', 204);
INSERT INTO public.triggers VALUES (527, 'corona', 204);
INSERT INTO public.triggers VALUES (528, 'virus', 204);
INSERT INTO public.triggers VALUES (529, 'covid', 204);
INSERT INTO public.triggers VALUES (530, 'covid19', 204);
INSERT INTO public.triggers VALUES (531, 'qu''est-ce qui est petit et marron ?', 205);
INSERT INTO public.triggers VALUES (532, 'petit', 205);
INSERT INTO public.triggers VALUES (533, 'qu''est-ce qui', 205);
INSERT INTO public.triggers VALUES (534, 'qu''est-ce que', 205);
INSERT INTO public.triggers VALUES (535, 'qu''est-ce', 205);
INSERT INTO public.triggers VALUES (536, 'rip', 206);
INSERT INTO public.triggers VALUES (537, 'pied de biche', 207);
INSERT INTO public.triggers VALUES (538, 'biche', 207);
INSERT INTO public.triggers VALUES (539, 'pied', 207);
INSERT INTO public.triggers VALUES (540, 'story', 208);
INSERT INTO public.triggers VALUES (541, 'romain', 209);
INSERT INTO public.triggers VALUES (542, 'roglin', 209);
INSERT INTO public.triggers VALUES (543, 'romain roglin', 209);
INSERT INTO public.triggers VALUES (544, 'tarte', 210);
INSERT INTO public.triggers VALUES (545, 'myrtille', 210);
INSERT INTO public.triggers VALUES (546, 'patisserie', 210);
INSERT INTO public.triggers VALUES (547, 'tarte a la myrtille', 210);
INSERT INTO public.triggers VALUES (548, 'hx5', 211);
INSERT INTO public.triggers VALUES (549, 'uther', 212);
INSERT INTO public.triggers VALUES (550, 'porteur de lumiere', 212);
INSERT INTO public.triggers VALUES (551, 'c''est la femme du soldat du duvet de la plume de l''oiseau du nid de la branche du pommier du jardin de ma tante', 213);
INSERT INTO public.triggers VALUES (552, 'et ce soldat il a une femme', 214);
INSERT INTO public.triggers VALUES (553, 'c''est le soldat du duvet de la plume de l''oiseau du nid de la branche du pommier du jardin de ma tante', 215);
INSERT INTO public.triggers VALUES (554, 'soldat', 215);
INSERT INTO public.triggers VALUES (555, 'et dans ce duvet il y a un soldat', 216);
INSERT INTO public.triggers VALUES (556, 'c''est le duvet de la plume de l''oiseau du nid de la branche du pommier du jardin de ma tante', 217);
INSERT INTO public.triggers VALUES (557, 'duvet', 217);
INSERT INTO public.triggers VALUES (558, 'et avec cette plume on fait un duvet', 218);
INSERT INTO public.triggers VALUES (559, 'c''est la plume de l''oiseau du nid de la branche du pommier du jardin de ma tante', 219);
INSERT INTO public.triggers VALUES (560, 'plume', 219);
INSERT INTO public.triggers VALUES (561, 'et cette oiseau il a une plume', 220);
INSERT INTO public.triggers VALUES (562, 'c''est l''oiseau du nid de la branche du pommier du jardin de ma tante', 221);
INSERT INTO public.triggers VALUES (563, 'oiseau', 221);
INSERT INTO public.triggers VALUES (564, 'et dans ce nid il y a un oiseau', 222);
INSERT INTO public.triggers VALUES (565, 'c''est le nid de la branche du pommier du jardin de ma tante', 223);
INSERT INTO public.triggers VALUES (566, 'nid', 223);
INSERT INTO public.triggers VALUES (567, 'et sur cette branche il y a un nid', 224);
INSERT INTO public.triggers VALUES (568, 'c''est la branche du pommier du jardin de ma tante', 225);
INSERT INTO public.triggers VALUES (569, 'branche', 225);
INSERT INTO public.triggers VALUES (570, 'et sur ce pommier il y a une branche', 226);
INSERT INTO public.triggers VALUES (571, 'c''est le pommier du jardin de ma tante', 227);
INSERT INTO public.triggers VALUES (572, 'pommier', 227);
INSERT INTO public.triggers VALUES (573, 'chez ma tante il y a un pommier', 227);
INSERT INTO public.triggers VALUES (574, 'et dans son jardin il y a un pommier', 228);
INSERT INTO public.triggers VALUES (575, 'tout ca grace a ma tante', 229);
INSERT INTO public.triggers VALUES (576, 'tante', 229);
INSERT INTO public.triggers VALUES (577, 'c''est le jardin de ma tante', 230);
INSERT INTO public.triggers VALUES (578, 'c''est le jardin a ma tante', 230);
INSERT INTO public.triggers VALUES (579, 'jardin', 230);
INSERT INTO public.triggers VALUES (580, 'i like train', 231);
INSERT INTO public.triggers VALUES (581, 'do you like trains?', 232);
INSERT INTO public.triggers VALUES (582, 'batman', 233);
INSERT INTO public.triggers VALUES (583, 'your bruce wayne', 234);
INSERT INTO public.triggers VALUES (584, 'bruce wayne', 234);
INSERT INTO public.triggers VALUES (585, 'you''re bruce wayne', 234);
INSERT INTO public.triggers VALUES (586, 'why?', 235);
INSERT INTO public.triggers VALUES (587, 'why', 235);
INSERT INTO public.triggers VALUES (588, 'i''m your father', 236);
INSERT INTO public.triggers VALUES (589, 'father', 236);
INSERT INTO public.triggers VALUES (590, 'je suis ton pere', 236);
INSERT INTO public.triggers VALUES (591, 'pornhub', 237);
INSERT INTO public.triggers VALUES (592, ' &#65279;j''aime les mjs', 237);
INSERT INTO public.triggers VALUES (593, 'croziflette ', 238);
INSERT INTO public.triggers VALUES (594, 'pancake', 239);
INSERT INTO public.triggers VALUES (595, 'i am the senate', 240);
INSERT INTO public.triggers VALUES (596, 'senate', 240);
INSERT INTO public.triggers VALUES (597, 'palpatine', 240);
INSERT INTO public.triggers VALUES (598, 'emperor', 240);
INSERT INTO public.triggers VALUES (599, 'hx3', 241);
INSERT INTO public.triggers VALUES (600, 'i am inevitable', 242);
INSERT INTO public.triggers VALUES (601, 'thanos', 242);
INSERT INTO public.triggers VALUES (602, 'star wars', 243);
INSERT INTO public.triggers VALUES (603, 'mj', 244);
INSERT INTO public.triggers VALUES (604, 'mjs', 244);
INSERT INTO public.triggers VALUES (605, 'maitres du jeu', 244);
INSERT INTO public.triggers VALUES (606, 'mort', 245);
INSERT INTO public.triggers VALUES (607, 'morts', 245);
INSERT INTO public.triggers VALUES (608, 'situation', 246);
INSERT INTO public.triggers VALUES (609, 'quelle est votre situation ?', 246);
INSERT INTO public.triggers VALUES (610, 'qu''elle est votre situation ?', 246);
INSERT INTO public.triggers VALUES (611, 'c''est une bonne situation ca, bot?', 246);
INSERT INTO public.triggers VALUES (612, '42', 247);
INSERT INTO public.triggers VALUES (613, 'la vie, l''univers et le reste', 248);
INSERT INTO public.triggers VALUES (614, 'reponse universelle', 248);
INSERT INTO public.triggers VALUES (615, 'question universelle', 248);
INSERT INTO public.triggers VALUES (616, 'combien', 248);
INSERT INTO public.triggers VALUES (617, 'combien de', 248);
INSERT INTO public.triggers VALUES (618, 'la reponse a la vie', 248);
INSERT INTO public.triggers VALUES (619, 'quelle est  la reponse a la vie', 248);
INSERT INTO public.triggers VALUES (620, 'la reponse', 248);
INSERT INTO public.triggers VALUES (621, 'quelle est la reponse ?', 248);
INSERT INTO public.triggers VALUES (622, 'quelle est la reponse universelle ?', 248);
INSERT INTO public.triggers VALUES (623, 'quelle est la reponse universelle a la vie, l''univers et le reste ?', 248);
INSERT INTO public.triggers VALUES (624, 'comment', 249);
INSERT INTO public.triggers VALUES (625, 'de quelle maniere', 249);
INSERT INTO public.triggers VALUES (626, 'how to', 249);
INSERT INTO public.triggers VALUES (627, 'chaussette', 250);
INSERT INTO public.triggers VALUES (628, 'naheulbeuk', 250);
INSERT INTO public.triggers VALUES (629, 'et ca, c''est le', 251);
INSERT INTO public.triggers VALUES (630, 'nyctalope', 252);
INSERT INTO public.triggers VALUES (631, 'qu''est-ce que tu dis ', 253);
INSERT INTO public.triggers VALUES (632, 'quoi', 253);
INSERT INTO public.triggers VALUES (633, 'j''ai pas compris', 253);
INSERT INTO public.triggers VALUES (634, 'hein', 253);
INSERT INTO public.triggers VALUES (635, 'pc', 254);
INSERT INTO public.triggers VALUES (636, 'espci', 254);
INSERT INTO public.triggers VALUES (637, 'pc1', 254);
INSERT INTO public.triggers VALUES (638, 'pcn', 254);
INSERT INTO public.triggers VALUES (639, 'pceen', 254);
INSERT INTO public.triggers VALUES (640, 'pceenne', 254);
INSERT INTO public.triggers VALUES (641, 'partout ou l''on va', 255);
INSERT INTO public.triggers VALUES (642, 'partout ou l''on vaaa', 255);
INSERT INTO public.triggers VALUES (643, 'les gens nous demandent', 256);
INSERT INTO public.triggers VALUES (644, 'qui l''on est', 257);
INSERT INTO public.triggers VALUES (645, 'qui lon est', 257);
INSERT INTO public.triggers VALUES (646, 'qui on est', 257);
INSERT INTO public.triggers VALUES (647, 'd''ou l''on vient', 258);
INSERT INTO public.triggers VALUES (648, 'dou lon vient', 258);
INSERT INTO public.triggers VALUES (649, 'dou on vient', 258);
INSERT INTO public.triggers VALUES (650, 'd''ou on vient', 258);
INSERT INTO public.triggers VALUES (651, 'et on leur dit toujours', 259);
INSERT INTO public.triggers VALUES (652, 'on leur dit toujours', 259);
INSERT INTO public.triggers VALUES (653, 'et on dit toujours', 259);
INSERT INTO public.triggers VALUES (654, 'qu''on est les pc', 260);
INSERT INTO public.triggers VALUES (655, 'quon est les pc', 260);
INSERT INTO public.triggers VALUES (656, 'on est les pc', 260);
INSERT INTO public.triggers VALUES (657, 'les pc de vauquelin', 261);
INSERT INTO public.triggers VALUES (658, 'les pc vauquelin', 261);
INSERT INTO public.triggers VALUES (659, 'vauquelin', 261);
INSERT INTO public.triggers VALUES (660, 'et si on nous entend pas', 262);
INSERT INTO public.triggers VALUES (661, 'si on nous entend pas', 262);
INSERT INTO public.triggers VALUES (662, 'et si on entend pas', 262);
INSERT INTO public.triggers VALUES (663, 'on chante encore plus fort', 263);
INSERT INTO public.triggers VALUES (664, 'on crie encore plus fort', 263);
INSERT INTO public.triggers VALUES (665, 'on hurle encore plus fort', 263);
INSERT INTO public.triggers VALUES (666, 'encore plus fort', 263);
INSERT INTO public.triggers VALUES (667, 'plus fort', 263);
INSERT INTO public.triggers VALUES (668, 'pas dit bonjour', 264);
INSERT INTO public.triggers VALUES (669, 'tu as pas dit bonjour', 264);
INSERT INTO public.triggers VALUES (670, 'il a pas dit bonjour', 264);
INSERT INTO public.triggers VALUES (671, 'waouh', 265);
INSERT INTO public.triggers VALUES (672, 'waou', 265);
INSERT INTO public.triggers VALUES (673, 'tu n''as donc pas de coeur', 266);
INSERT INTO public.triggers VALUES (674, 'tu n''as pas de coeur', 266);
INSERT INTO public.triggers VALUES (675, 'bot sans coeur', 266);
INSERT INTO public.triggers VALUES (676, 'poulet', 267);
INSERT INTO public.triggers VALUES (677, 'marron caca', 268);
INSERT INTO public.triggers VALUES (678, 'marron', 268);
INSERT INTO public.triggers VALUES (679, 'caca', 268);
INSERT INTO public.triggers VALUES (680, 'la go la est peut etre une fille bien', 269);
INSERT INTO public.triggers VALUES (681, 'chocolatine', 270);
INSERT INTO public.triggers VALUES (682, 'pourquoi tu reponds pas ?', 271);
INSERT INTO public.triggers VALUES (683, 'changement d''heure', 272);
INSERT INTO public.triggers VALUES (684, 'parrain !', 273);
INSERT INTO public.triggers VALUES (685, 'je veux mon parrain', 273);
INSERT INTO public.triggers VALUES (686, '139', 274);
INSERT INTO public.triggers VALUES (687, 'qui sont les 139', 274);
INSERT INTO public.triggers VALUES (688, 'ou sont les 139', 274);
INSERT INTO public.triggers VALUES (689, 'qui sont les mj', 275);
INSERT INTO public.triggers VALUES (690, 'c''est qui les mj', 275);
INSERT INTO public.triggers VALUES (691, 'liste des mj', 275);
INSERT INTO public.triggers VALUES (692, 'noms des mj', 275);
INSERT INTO public.triggers VALUES (693, 'qui suis-je ?', 275);
INSERT INTO public.triggers VALUES (694, 'je suis qui ?', 275);
INSERT INTO public.triggers VALUES (695, 'repond-moi', 276);
INSERT INTO public.triggers VALUES (696, 'repond moi', 276);
INSERT INTO public.triggers VALUES (697, 'vasy repond moi', 276);
INSERT INTO public.triggers VALUES (698, 'resultats des votes', 277);
INSERT INTO public.triggers VALUES (699, 'joueurs loups', 278);
INSERT INTO public.triggers VALUES (700, 'joueurs loups garous', 278);
INSERT INTO public.triggers VALUES (701, 'qui sont les loups', 278);
INSERT INTO public.triggers VALUES (702, 'qui sont les loups-garous', 278);
INSERT INTO public.triggers VALUES (703, 'qui est loup', 278);
INSERT INTO public.triggers VALUES (704, 'qui est un loup', 278);
INSERT INTO public.triggers VALUES (705, 'qui est loup-garou', 278);
INSERT INTO public.triggers VALUES (706, 'c''est qui les loups-garous', 278);
INSERT INTO public.triggers VALUES (707, 'c''est qui les loups', 278);
INSERT INTO public.triggers VALUES (708, 'joueurs mv', 278);
INSERT INTO public.triggers VALUES (709, 'joueurs morts vivants', 278);
INSERT INTO public.triggers VALUES (710, 'qui sont les mv', 278);
INSERT INTO public.triggers VALUES (711, 'qui sont les morts vivants', 278);
INSERT INTO public.triggers VALUES (712, 'c''est qui les morts vivants', 278);
INSERT INTO public.triggers VALUES (713, 'c''est qui les mv', 278);
INSERT INTO public.triggers VALUES (714, 'qui est un mv', 278);
INSERT INTO public.triggers VALUES (715, 'qui est mort vivant', 278);
INSERT INTO public.triggers VALUES (716, 'quel est mon role ?', 279);
INSERT INTO public.triggers VALUES (717, 'que suis-je ?', 279);
INSERT INTO public.triggers VALUES (718, 'c''est quoi mon role ?', 279);
INSERT INTO public.triggers VALUES (719, 'je suis quoi ?', 279);
INSERT INTO public.triggers VALUES (720, 'j''ai oublie mon role', 279);
INSERT INTO public.triggers VALUES (721, 'meteo', 280);
INSERT INTO public.triggers VALUES (722, 'quel temps va-t-il faire', 280);
INSERT INTO public.triggers VALUES (723, 'va t''il pleuvoir', 280);
INSERT INTO public.triggers VALUES (724, 'y a-t-il de la pluie de prevu', 280);
INSERT INTO public.triggers VALUES (725, 'circulation', 281);
INSERT INTO public.triggers VALUES (726, 'bouchons', 281);
INSERT INTO public.triggers VALUES (727, 'metro', 281);
INSERT INTO public.triggers VALUES (728, 'dis quelquechose', 282);
INSERT INTO public.triggers VALUES (729, 'dis quelquchose', 282);
INSERT INTO public.triggers VALUES (730, 'dis quelque chose', 282);
INSERT INTO public.triggers VALUES (731, 'quelle est ta couleur preferee ?', 283);
INSERT INTO public.triggers VALUES (732, 'qui va gagner ?', 284);
INSERT INTO public.triggers VALUES (733, 'qui meurt ce soir ?', 285);
INSERT INTO public.triggers VALUES (734, 'qui va mourir en premier ?', 286);
INSERT INTO public.triggers VALUES (735, 'jusqu''ou va-t-on ?', 287);
INSERT INTO public.triggers VALUES (736, 'quels sont les roles des joueurs ?', 288);
INSERT INTO public.triggers VALUES (737, 'pourquoi la vie?', 289);
INSERT INTO public.triggers VALUES (738, 'bdo', 290);
INSERT INTO public.triggers VALUES (739, 'la bdo', 290);
INSERT INTO public.triggers VALUES (740, 'gri', 291);
INSERT INTO public.triggers VALUES (741, 'gris', 291);
INSERT INTO public.triggers VALUES (742, 'pouet', 292);
INSERT INTO public.triggers VALUES (743, 'fanfare', 292);
INSERT INTO public.triggers VALUES (744, 'ggm', 292);
INSERT INTO public.triggers VALUES (745, 'leopard', 292);
INSERT INTO public.triggers VALUES (746, 'le bar', 293);
INSERT INTO public.triggers VALUES (747, 'le bar !!!', 293);
INSERT INTO public.triggers VALUES (748, 'le bar 👊', 293);
INSERT INTO public.triggers VALUES (749, '👊', 293);
INSERT INTO public.triggers VALUES (750, 'moulin', 294);
INSERT INTO public.triggers VALUES (751, 'delice', 294);
INSERT INTO public.triggers VALUES (752, 'moulin des delices', 294);
INSERT INTO public.triggers VALUES (753, 'lange', 295);
INSERT INTO public.triggers VALUES (754, 'le lange', 295);
INSERT INTO public.triggers VALUES (755, 'langevinium', 295);
INSERT INTO public.triggers VALUES (756, 'le langevinium', 295);
INSERT INTO public.triggers VALUES (757, 'bottom', 296);
INSERT INTO public.triggers VALUES (758, 'gisele', 297);
INSERT INTO public.triggers VALUES (759, 'courgettes', 298);
INSERT INTO public.triggers VALUES (760, 'panda', 299);
INSERT INTO public.triggers VALUES (761, '&#65279;je m''appelle la petite bestiole.', 300);
INSERT INTO public.triggers VALUES (762, '&#65279;bestiole', 300);
INSERT INTO public.triggers VALUES (763, 'squiq', 301);
INSERT INTO public.triggers VALUES (764, 'scroutch', 301);
INSERT INTO public.triggers VALUES (765, 'ecureuil', 302);
INSERT INTO public.triggers VALUES (766, 'petit ecureuil', 302);
INSERT INTO public.triggers VALUES (767, 'llama', 303);
INSERT INTO public.triggers VALUES (768, 'pipocampe', 304);
INSERT INTO public.triggers VALUES (769, 'pippocampe', 304);
INSERT INTO public.triggers VALUES (770, 'la deferlante', 305);
INSERT INTO public.triggers VALUES (771, 'la def', 305);
INSERT INTO public.triggers VALUES (772, 'olympe', 306);
INSERT INTO public.triggers VALUES (773, 'l''olympe', 306);
INSERT INTO public.triggers VALUES (774, 'cavalerie', 307);
INSERT INTO public.triggers VALUES (775, 'cav', 307);
INSERT INTO public.triggers VALUES (776, 'cav''', 307);
INSERT INTO public.triggers VALUES (777, 'l''escadrille', 308);
INSERT INTO public.triggers VALUES (778, 'escadrille', 308);
INSERT INTO public.triggers VALUES (779, 'neb', 309);
INSERT INTO public.triggers VALUES (780, 'nebuleuse', 309);
INSERT INTO public.triggers VALUES (781, 'la neb', 309);
INSERT INTO public.triggers VALUES (782, 'la nebuleuse', 309);
INSERT INTO public.triggers VALUES (783, 'épée', 192);
INSERT INTO public.triggers VALUES (784, 'épées', 192);
INSERT INTO public.triggers VALUES (785, 'dis paramedical', 15);
INSERT INTO public.triggers VALUES (786, '(╯°□°）╯︵ ┻━┻', 8);
INSERT INTO public.triggers VALUES (787, '┬─┬ ノ( ゜-゜ノ)', 16);


--
-- Name: actions__id_seq; Type: SEQUENCE SET; Schema: public; Owner: lg-rez
--

SELECT pg_catalog.setval('public.actions__id_seq', 2, true);


--
-- Name: base_actions_roles_id_seq; Type: SEQUENCE SET; Schema: public; Owner: lg-rez
--

SELECT pg_catalog.setval('public.base_actions_roles_id_seq', 1, false);


--
-- Name: joueurs_discord_id_seq; Type: SEQUENCE SET; Schema: public; Owner: lg-rez
--

SELECT pg_catalog.setval('public.joueurs_discord_id_seq', 1, false);


--
-- Name: reactions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: lg-rez
--

SELECT pg_catalog.setval('public.reactions_id_seq', 16, true);


--
-- Name: triggers_id_seq; Type: SEQUENCE SET; Schema: public; Owner: lg-rez
--

SELECT pg_catalog.setval('public.triggers_id_seq', 787, true);


--
-- Name: actions actions_pkey; Type: CONSTRAINT; Schema: public; Owner: lg-rez
--

ALTER TABLE ONLY public.actions
    ADD CONSTRAINT actions_pkey PRIMARY KEY (_id);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: lg-rez
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: base_actions base_actions_pkey; Type: CONSTRAINT; Schema: public; Owner: lg-rez
--

ALTER TABLE ONLY public.base_actions
    ADD CONSTRAINT base_actions_pkey PRIMARY KEY (action);


--
-- Name: base_actions_roles base_actions_roles_pkey; Type: CONSTRAINT; Schema: public; Owner: lg-rez
--

ALTER TABLE ONLY public.base_actions_roles
    ADD CONSTRAINT base_actions_roles_pkey PRIMARY KEY (id);


--
-- Name: joueurs joueurs_pkey; Type: CONSTRAINT; Schema: public; Owner: lg-rez
--

ALTER TABLE ONLY public.joueurs
    ADD CONSTRAINT joueurs_pkey PRIMARY KEY (discord_id);


--
-- Name: reactions reactions_pkey; Type: CONSTRAINT; Schema: public; Owner: lg-rez
--

ALTER TABLE ONLY public.reactions
    ADD CONSTRAINT reactions_pkey PRIMARY KEY (id);


--
-- Name: roles roles_pkey; Type: CONSTRAINT; Schema: public; Owner: lg-rez
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_pkey PRIMARY KEY (slug);


--
-- Name: triggers triggers_pkey; Type: CONSTRAINT; Schema: public; Owner: lg-rez
--

ALTER TABLE ONLY public.triggers
    ADD CONSTRAINT triggers_pkey PRIMARY KEY (id);


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: lg-rez
--

REVOKE ALL ON SCHEMA public FROM postgres;
REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT ALL ON SCHEMA public TO "lg-rez";


--
-- PostgreSQL database dump complete
--

