import React from 'react';
import {Route, Switch} from "react-router-dom";
import PropTypes from 'prop-types';

import ContrastOverviewView from "Roger/views/contrast/overview";
import {NotFound} from "Roger/views/not_found";


class ContrastRouter extends React.Component {
    constructor(props) {
        super(props);
        this.state = {studyComp: []};
    }

    render() {
        const {study, sampleAnnotation, contrast, studyBaseURL, contrastBaseURL} = this.props;
        return <Switch>
            <Route exact path={`${contrastBaseURL}/`}
                   render={() =>
                       <ContrastOverviewView
                           study={study}
                           sampleAnnotation={sampleAnnotation}
                           contrast={contrast}
                           studyBaseURL={studyBaseURL}/>
                   }/>
            <Route component={NotFound}/>
        </Switch>;
    }
}

ContrastRouter.propTypes = {
    study: PropTypes.object.isRequired,
    sampleAnnotation: PropTypes.object.isRequired,
    design: PropTypes.object.isRequired,
    contrast: PropTypes.object.isRequired,
    studyBaseURL: PropTypes.string.isRequired,
    contrastBaseURL: PropTypes.string.isRequired
};

export default ContrastRouter;