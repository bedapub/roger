import React from 'react';
import {Route, Switch} from "react-router-dom";

import StudyOverview from "Roger/views/study/overview";
import GeneExpression from "Roger/views/study/gene_expression";

import DesignOverview from "Roger/views/design/overview";

import {URL_PREFIX} from "Roger/logic/rest";
import {NotFound} from "Roger/views/not_found";


class SingleStudy extends React.Component {
    constructor(props) {
        super(props);
        this.state = {studyComp: []};
    }

    componentDidMount() {
        const {studyName, url} = this.props;
        Promise.all([
            fetch(`${URL_PREFIX}/study/${studyName}`),
            fetch(`${URL_PREFIX}/study/${studyName}/sample_annotation/json`)
        ])
            .then(([res1, res2]) => Promise.all([res1.json(), res2.json()]))
            .then(([study, sampleAnnotation]) => {
                let studyComp =
                    <Switch>
                        <Route exact path={`${url}/`}
                               render={() =>
                                   <StudyOverview
                                       study={study}
                                       sampleAnnotation={sampleAnnotation}
                                       basePath={url}/>
                               }/>
                        <Route exact path={`${url}/expression`}
                               render={() =>
                                   <GeneExpression
                                       study={study}
                                       sampleAnnotation={sampleAnnotation}
                                       basePath={url}/>
                               }/>
                        {study.Design.map(design =>
                            <Route key={design.Name} path={`${url}/design/${design.Name}`}
                                   render={() =>
                                       <DesignOverview
                                           study={study}
                                           sampleAnnotation={sampleAnnotation}
                                           design={design}
                                           basePath={url}/>
                                   }/>
                        )}
                        <Route component={NotFound}/>
                    </Switch>;
                this.setState({studyComp: studyComp});
            });
    }

    render() {
        return this.state.studyComp;
    }
}


export const SingleStudyView = ({match}) => <SingleStudy studyName={match.params.studyName} url={match.url}/>;