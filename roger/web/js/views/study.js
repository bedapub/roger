import React from 'react';
import {URL_PREFIX} from "../logic/rest";
import Plot from "react-plotly.js";
import './loading_spinner.css';
import "isomorphic-fetch"

class DGE_PCA_Plot extends React.Component {
    constructor(props) {
        super(props);
        this.state = {loaded: false, renderedComp: []};
    }

    componentDidMount() {
        fetch(`${URL_PREFIX}/study/${this.props.studyName}`
            + `/design/${this.props.designName}`
            + `/contrast/${this.props.contrastName}`
            + `/dge/${this.props.dgeMethodName}/plot/pca`)
            .then(result => result.json())
            .then(pca_data => {
                let studyComp =
                    <Plot
                        data={pca_data.data}
                        layout={pca_data.layout}
                    />;
                this.setState({loaded: true, renderedComp: studyComp});
            });
    }

    render() {
        return this.state.loaded ? this.state.renderedComp : SpinnerAnimation;
    }
}

const SpinnerAnimation =
    <div className="lds-ring">
        <div/>
        <div/>
        <div/>
        <div/>
    </div>;

class StudyOverview extends React.Component {
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
            .then(([study, sample_annotation]) => {
                console.log(sample_annotation.data.map(row => row['SAMPLE']));
                let studyComp = <div key={study.Name} className="info_container">
                    <p><span>Name:</span> {study.Name}</p>
                    <ul>
                        <li>
                            <span>Expression type:</span> {study.ExpressionType}
                        </li>
                        <li>
                            <span>Description:</span> {study.Description}
                        </li>
                        <li>
                            <span>Sample count:</span> {study.SampleCount}
                        </li>
                        <li>
                            <span>Feature count:</span> {study.FeatureCount}
                        </li>
                        <li>
                            <span>Gene annotation version:</span> {study.GeneAnnotationVersion}
                        </li>
                        <li>
                            <span>Created by :</span> {study.CreatedBy}
                        </li>
                    </ul>
                    <span>Designs:</span>
                    <div>
                        {study.Design.map(design => (
                            <div key={design.Name} className="info_container">
                                <p><span>Name:</span> {design.Name}</p>
                                <ul>
                                    <li>
                                        <span>Description:</span> {design.Description}
                                    </li>
                                    <li>
                                        <span>Variable Count:</span> {design.VariableCount}
                                    </li>
                                    <li>
                                        <span>Last Reviewed by:</span> {design.LastReviewedBy}
                                    </li>
                                    <li>
                                        <span>Created by: </span> {design.CreatedBy}
                                    </li>
                                    <li>
                                        <span>Used Samples: </span>
                                        {StudyOverview.countSampleSubset(design.SampleSubset)} of {study.SampleCount}
                                    </li>
                                </ul>
                                <span>Contrasts:</span>
                                {design.Contrast.map(contrast => (
                                    <div key={contrast.Name} className="info_container">
                                        <p><span>Name:</span> {contrast.Name}</p>
                                        <ul>
                                            <li>
                                                <span>Description:</span> {contrast.Description}
                                            </li>
                                            <li>
                                                <span>Created by: </span> {design.CreatedBy}
                                            </li>
                                        </ul>
                                        <span>DGE Results:</span>
                                        {contrast.DGEmodel.map(dgeResult => (
                                            <div
                                                key={`${study.Name}_${design.Name}__${contrast.Name}__${dgeResult.MethodName}`}
                                                className="info_container">
                                                <p><span>Name:</span> {dgeResult.MethodName}</p>
                                                <ul>
                                                    <li>
                                                        <span>Method Description:</span> {dgeResult.MethodDescription}
                                                    </li>
                                                    <DGE_PCA_Plot studyName={study.Name}
                                                                  designName={design.Name}
                                                                  contrastName={contrast.Name}
                                                                  dgeMethodName={dgeResult.MethodName}/>
                                                </ul>
                                            </div>
                                        ))}
                                    </div>
                                ))}
                            </div>
                        ))}
                    </div>
                </div>;
                this.setState({studyComp: studyComp});
            });
    }

    render() {
        return this.state.studyComp;
    }

    static countSampleSubset(sampleSubset) {
        return sampleSubset.filter(entry => entry.IsUsed).length
    }
}

export const SingleStudyView = ({match}) => <StudyOverview studyName={match.params.study_name}/>;