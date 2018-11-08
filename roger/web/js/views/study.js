import React from 'react';
import {Route, Switch} from "react-router-dom";

import StudyOverview from "./study/overview";
import DesignOverview from "./study/design/overview";

import {URL_PREFIX} from "../logic/rest";
import {NotFound} from "./not_found";


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
                               render={(props) =>
                                   <StudyOverview {...props}
                                                  study={study}
                                                  sampleAnnotation={sampleAnnotation}/>
                               }/>
                        <Route exact path={`${url}/design/:designName`}
                               render={(props) =>
                                   <DesignOverview study={study} sampleAnnotation={sampleAnnotation}
                                                   design={study.Design.find(e => e.Name === props.match.params.designName)}
                                                   basePath={url}/>
                               }/>
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