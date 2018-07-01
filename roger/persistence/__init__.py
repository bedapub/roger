import roger.persistence.geneanno


def init_db(db):
    db.create_all()
    roger.persistence.geneanno.add_species(db.session(),
                                           roger.persistence.geneanno.human_dataset,
                                           roger.persistence.geneanno.human_tax_id)
