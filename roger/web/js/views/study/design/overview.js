import React from 'react';
import PropTypes from 'prop-types';

import StudyDrawer from "../../../components/study/study_drawer";
import DesignTable from "../../../components/design/design_table";

function DesignOverview(props) {
    const {study, design, sampleAnnotation, basePath} = props;

    return (
        <StudyDrawer study={study} basePath={basePath}>
            <DesignTable
                design={design}
                sampleAnnotation={sampleAnnotation}/>
        </StudyDrawer>
    );
}

DesignOverview.propTypes = {
    design: PropTypes.object.isRequired,
    sampleAnnotation: PropTypes.object.isRequired,
    basePath: PropTypes.string.isRequired
};

export default DesignOverview;