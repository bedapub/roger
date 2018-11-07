import React from 'react';

import StudyDrawer from "../components/study/study_drawer";
import StudyOverview from "../components/study/general/overview";
import {URL_PREFIX} from "../logic/rest";


class SingleStudy extends React.Component {
    constructor(props) {
        super(props);
        this.state = {studyComp: []};
    }

    componentDidMount() {
        Promise.all([
            fetch(`${URL_PREFIX}/study/${this.props.studyName}`),
            fetch(`${URL_PREFIX}/study/${this.props.studyName}/sample_annotation/json`)
        ])
            .then(([res1, res2]) => Promise.all([res1.json(), res2.json()]))
            .then(([study, sampleAnnotation]) => {
                let studyComp =
                    <StudyDrawer study={study}>
                        <StudyOverview study={study} sampleAnnotation={sampleAnnotation}/>
                    </StudyDrawer>;
                this.setState({studyComp: studyComp});
            });
    }

    render() {
        return this.state.studyComp;
    }
}


export const SingleStudyView = ({match}) => <SingleStudy studyName={match.params.studyName}/>;