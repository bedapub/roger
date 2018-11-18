import React from 'react';
import {Route, Switch} from "react-router-dom";
import PropTypes from 'prop-types';

import DGEView from "Roger/views/contrast/dge"
import GSEView from "Roger/views/contrast/gse"
import ContrastOverviewView from "Roger/views/contrast/overview";
import {NotFound} from "Roger/views/not_found";


class ContrastRouter extends React.Component {
    constructor(props) {
        super(props);
        this.state = {studyComp: []};
    }

    render() {
        const {study, sampleAnnotation, design, contrast, contrastColumn, studyBaseURL, contrastBaseURL} = this.props;
        return <Switch>
            <Route exact path={`${contrastBaseURL}/`}
                   render={() =>
                       <ContrastOverviewView
                           study={study}
                           sampleAnnotation={sampleAnnotation}
                           contrast={contrast}
                           studyBaseURL={studyBaseURL}/>
                   }/>
            {contrast.DGEmodel.map(dgeResult =>
                <Route key={dgeResult.MethodName}
                       exact path={`${contrastBaseURL}/dge/${dgeResult.MethodName}`}
                       render={() =>
                           <DGEView
                               study={study}
                               sampleAnnotation={sampleAnnotation}
                               design={design}
                               contrast={contrast}
                               contrastColumn={contrastColumn}
                               dgeResult={dgeResult}
                               studyBaseURL={studyBaseURL}/>
                       }/>
            )}
            {contrast.GSEresult.map(gseResult =>
                <Route key={`${gseResult.DGEMethodName}_${gseResult.GSEMethodName}`}
                       exact path={`${contrastBaseURL}/dge/${gseResult.DGEMethodName}/gse/${gseResult.GSEMethodName}`}
                       render={() =>
                           <GSEView
                               study={study}
                               sampleAnnotation={sampleAnnotation}
                               contrast={contrast}
                               studyBaseURL={studyBaseURL}/>
                       }/>
            )}
            <Route component={NotFound}/>
        </Switch>;
    }
}

ContrastRouter.propTypes = {
    study: PropTypes.object.isRequired,
    sampleAnnotation: PropTypes.object.isRequired,
    design: PropTypes.object.isRequired,
    contrast: PropTypes.object.isRequired,
    contrastColumn: PropTypes.object.isRequired,
    studyBaseURL: PropTypes.string.isRequired,
    contrastBaseURL: PropTypes.string.isRequired
};

export default ContrastRouter;