def community_rename_for_folder(community_raw) -> str:

    community = ""

    if community_raw == "Andalucía":
        community = "Andalucia"

    elif community_raw == "Aragón":
        community = "Aragon"

    elif community_raw == "Principado de Asturias":
        community = "Asturias"

    elif community_raw == "Castilla-La Mancha":
        community = "CastillaLaMancha"

    elif community_raw == "Castilla y León":
        community = "CastillaLeon"

    elif community_raw == "Cataluña":
        community = "Cataluna"

    elif community_raw == "Comunidad de Madrid":
        community = "Madrid"

    elif community_raw == "Comunidad Valenciana":
        community = "Valencia"

    elif community_raw == "La Rioja":
        community = "LaRioja"

    elif community_raw == "Islas Baleares":
        community = "Baleares"
    elif community_raw == "Comunidad Foral de Navarra":
        community = "Navarra"
    elif community_raw == "Región de Murcia":
        community = "Murcia"

    elif community_raw == "País Vasco":
        community = "PaisVasco"

    else:
        community = str(community_raw)

    return community


def subject_rename(subject_raw):
    subject = ""
    if subject_raw == "Biología":
        subject = "biology"
    elif subject_raw == "Historia de la Filosofía":
        subject = "philosofy"
    elif subject_raw == "Inglés":
        subject = "english"
    elif subject_raw == "Lengua y literatura":
        subject = "language"
    elif subject_raw == "Historia":
        subject = "history"
    elif subject_raw == "Matemáticas científicas":
        subject = "scientistMath"
    elif subject_raw == "Matemáticas sociales":
        subject = "socialsMath"
    elif subject_raw == "Química":
        subject = "chemistry"
    elif subject_raw == "Física":
        subject = "physics"
    elif subject_raw == "Historia del Arte":
        subject = "artHistory"
    elif subject_raw == "Economía":
        subject = "economy"

    return subject


def join_path_subject(path, subject_raw, community, prompt) -> str:

    subject = ""
    if subject_raw == "Biología":
        subject = "biology"
    elif subject_raw == "Historia de la Filosofía":
        subject = "philosofy"
    elif subject_raw == "Inglés":
        subject = "english"
    elif subject_raw == "Lengua y literatura":
        subject = "language"
    elif subject_raw == "Historia":
        subject = "history"
    elif subject_raw == "Matemáticas científicas":
        subject = "scientistMath"
    elif subject_raw == "Matemáticas sociales":
        subject = "socialsMath"
    elif subject_raw == "Historia del Arte":
        subject = "artHistory"
    elif subject_raw == "Economía":
        subject = "economy"

    elif subject_raw == "Química":
        subject = "chemistry"
    elif subject_raw == "Física":
        subject = "physics"

    if prompt == False:
        final_path = path + subject + "_" + community.lower() + ".pdf"
    else:
        final_path = path + subject + "_" + community.lower() + ".txt"

    return final_path
