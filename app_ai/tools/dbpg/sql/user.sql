CREATE TABLE public.users (
	user_id int4 DEFAULT nextval('users_id_seq'::regclass) NOT NULL,
	user_ip_adress varchar(50) NULL,
	username varchar(50) NOT NULL,
	password_hash text NOT NULL,
	created_at timestamp DEFAULT now() NOT NULL,
	last_login timestamp NULL,
	e_mail varchar(300) NULL,
	last_name varchar(300) NULL,
	first_name varchar(300) NULL,
	surname varchar(300) NULL,
	avatar varchar(500) NULL,
	CONSTRAINT uc_email UNIQUE (e_mail),
	CONSTRAINT users_pkey PRIMARY KEY (user_id),
	CONSTRAINT users_username_key UNIQUE (username)
);
CREATE INDEX idx_email ON public.users USING btree (e_mail);
CREATE INDEX idx_names ON public.users USING btree (last_name, first_name);
CREATE INDEX idx_users_username ON public.users USING btree (username);