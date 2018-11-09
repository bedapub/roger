import React from 'react';
import {Link, Route, Switch} from "react-router-dom";
import PropTypes from 'prop-types';

import DesignOverviewView from "Roger/views/design/overview";
import ContrastRouter from "Roger/views/contrast/router";
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
                       <DesignOverviewView
                           study={study}
                           sampleAnnotation={sampleAnnotation}
                           design={design}
                           basePath={studyBaseURL}/>
                   }/>
            {design.Contrast.map(contrast =>
                <Route key={contrast.Name} path={`${designBaseURL}/contrast/${contrast.Name}`}
                       render={() =>
                           <ContrastRouter
                               study={study}
                               sampleAnnotation={sampleAnnotation}
                               design={design}
                               contrast={contrast}
                               studyBaseURL={studyBaseURL}
                               contrastBaseURL={`${designBaseURL}/contrast/${contrast.Name}`}/>
                       }/>
            )}
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