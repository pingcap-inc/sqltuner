create table history (
    id bigint not null auto_increment,
    original_sql text,
    schemas_info text,
    execution_plan text,
    tuned_sql text,
    what_changed text,
    index_suggestion text,
    correct tinyint,
    gpt_version varchar(20),
    created_at timestamp not null default current_timestamp,
    primary key (id)
    );
