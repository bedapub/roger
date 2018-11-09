from roger.logic.mart import AnnotationService

# TODO make use of current_app instead (http://flask.pocoo.org/docs/1.0/appcontext)

# This is needed to do lazy loading / boost startup time
__initialized = False
__annotation_service = None
__app = None


def __create_instance():
    annotation_service_type = "ENSEMBL"
    if 'ROGER_ANNOTATION_SERVICE' in __app.config:
        annotation_service_type = __app.config['ROGER_ANNOTATION_SERVICE']
    if annotation_service_type == 'ENSEMBL':
        from roger.logic.mart.remote_mart import RemoteEnsemblBioMartService
        return RemoteEnsemblBioMartService()
    elif annotation_service_type == 'LOCAL':
        from roger.logic.mart.local_mart import LocalEnsemblBioMartService
        return LocalEnsemblBioMartService(
            __app.config.get('ROGER_ANNOTATION_DBHOST', None),
            __app.config.get('ROGER_ANNOTATION_DBPORT', None),
            __app.config.get('ROGER_ANNOTATION_DBUSER', None),
            __app.config.get('ROGER_ANNOTATION_DBPASSWD', None),
            __app.config.get('ROGER_ANNOTATION_DB', None)
        )
    else:
        raise RuntimeError("Unknown annotation service type: %s" % annotation_service_type)


def init_annotation_service(app):
    global __app
    __app = app


def get_annotation_service() -> AnnotationService:
    global __annotation_service
    global __initialized

    if not __initialized:
        __annotation_service = __create_instance()
        __initialized = True
    return __annotation_service
