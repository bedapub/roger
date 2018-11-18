import React from 'react';
import {Route, Switch} from "react-router-dom";
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
                contrast.ContrastColumn.map(contrastColumn =>
                    <Route key={contrastColumn.Name} path={`${designBaseURL}/contrast/${contrastColumn.Name}`}
                           render={() =>
                               <ContrastRouter
                                   study={study}
                                   sampleAnnotation={sampleAnnotation}
                                   design={design}
                                   contrast={contrast}
                                   contrastColumn={contrastColumn}
                                   studyBaseURL={studyBaseURL}
                                   contrastBaseURL={`${designBaseURL}/contrast/${contrastColumn.Name}`}/>
                           }/>
                )
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