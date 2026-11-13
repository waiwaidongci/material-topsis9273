
CREATE TABLE retest_records (
	id INTEGER NOT NULL AUTO_INCREMENT,
	note_id INTEGER NOT NULL,
	metric VARCHAR(30) NOT NULL,
	sample_code VARCHAR(40) NOT NULL,
	`value` DOUBLE,
	unit VARCHAR(50) NOT NULL,
	batch VARCHAR(100) NOT NULL,
	submitted_by VARCHAR(140) NOT NULL,
	created_at DATETIME NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (note_id, metric, sample_code),
	FOREIGN KEY(note_id) REFERENCES trial_notes (id)
)

;


CREATE TABLE retest_analyses (
	id INTEGER NOT NULL AUTO_INCREMENT,
	note_id INTEGER NOT NULL,
	version INTEGER NOT NULL,
	created_by VARCHAR(140) NOT NULL,
	detail JSON NOT NULL,
	created_at DATETIME NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (note_id, version),
	FOREIGN KEY(note_id) REFERENCES trial_notes (id)
)

;
