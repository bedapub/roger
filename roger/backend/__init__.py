import roger.backend.geneanno


def init_db(db):
    db.create_all()
    roger.backend.geneanno.add_species(db.session(),
                                       roger.backend.geneanno.human_dataset,
                                       roger.backend.geneanno.human_tax_id)
