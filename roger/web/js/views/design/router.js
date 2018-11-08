import React from 'react';
import {Route, Switch} from "react-router-dom";
import PropTypes from 'prop-types';

import DesignOverview from "Roger/views/design/overview";
import {NotFound} from "Roger/views/not_found";


class DesignRouter extends React.Component {
    constructor(props) {
        super(props);
        this.state = {studyComp: []};
    }

    render() {
        const {study, sampleAnnotation, design, studyBaseURL, designBaseURL} = this.props;
        return <Switch>
            <Route exact path={`${designBaseURL}/`}
                   render={() =>
                       <DesignOverview
                           study={study}
                           sampleAnnotation={sampleAnnotation}
                           design={design}
                           basePath={studyBaseURL}/>
                   }/>
            <Route component={NotFound}/>
        </Switch>;
    }
}

DesignRouter.propTypes = {
    study: PropTypes.object.isRequired,
    sampleAnnotation: PropTypes.object.isRequired,
    design: PropTypes.object.isRequired,
    studyBaseURL: PropTypes.string.isRequired,
    designBaseURL: PropTypes.string.isRequired
};

export default DesignRouter;