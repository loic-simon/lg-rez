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
    reponse character varying(500) NOT NULL
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
INSERT INTO public.reactions VALUES (8, '┬─┬ ノ( ゜-゜ノ)');
INSERT INTO public.reactions VALUES (9, 'Pierre ! <||> Feuille ! <||> Ciseaux !');


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
INSERT INTO public.triggers VALUES (24, '(+deg#deg)+( +-+', 8);
INSERT INTO public.triggers VALUES (25, 'ferme ta mouille', 7);
INSERT INTO public.triggers VALUES (26, 'pierre', 9);
INSERT INTO public.triggers VALUES (27, 'feuille', 9);
INSERT INTO public.triggers VALUES (28, 'ciseau', 9);
INSERT INTO public.triggers VALUES (29, 'ciseaux', 9);


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

SELECT pg_catalog.setval('public.reactions_id_seq', 13, true);


--
-- Name: triggers_id_seq; Type: SEQUENCE SET; Schema: public; Owner: lg-rez
--

SELECT pg_catalog.setval('public.triggers_id_seq', 29, true);


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

