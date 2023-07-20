create table history (
    id bigint not null auto_increment,
    original_sql text,
    schemas_info text,
    stats_info text,
    tuned_sql text,
    what_changed text,
    index_suggestion text,
    correct tinyint,
    primary key (id)
    );