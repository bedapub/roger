import React from 'react';
import ReactDOM from 'react-dom';
import {BrowserRouter as Router, Route, Link, Switch} from "react-router-dom";

import {URL_PREFIX} from "../components/rest";


class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            hasError: false,
            error: null,
            errorInfo: null
        };
    }

    componentDidCatch(error, info) {
        // Display fallback UI
        this.setState({hasError: true, error: error, errorInfo: info});
    }

    render() {
        if (this.state.hasError) {
            // You can render any custom fallback UI
            return (
                <div>
                    <h1>Something went wrong.</h1>
                    <details open style={{whiteSpace: 'pre-wrap'}}>
                        {this.state.error && this.state.error.toString()}
                        <br/>
                        {this.state.errorInfo.componentStack}
                    </details>
                </div>
            );
        }
        return this.props.children;
    }
}

class StudyList extends React.Component {
    constructor() {
        super();
        this.state = {items: []};
    }

    componentDidMount() {
        fetch(`${URL_PREFIX}/study`)
            .then(result => result.json())
            .then(items => {
                this.setState({items: items});
            });
    }

    render() {
        return (
            <div>
                {this.state.items.map(item => (
                    <div key={item.Name} className="info_container">
                        <p><span>Name:</span> <Link to={`/study/${item.Name}`}>{item.Name}</Link></p>
                        <ul>
                            <li>
                                <span>Expression type:</span> {item.ExpressionType}
                            </li>
                            <li>
                                <span>Description:</span> {item.Description}
                            </li>
                            <li>
                                <span>Sample count:</span> {item.SampleCount}
                            </li>
                            <li>
                                <span>Feature count:</span> {item.FeatureCount}
                            </li>
                            <li>
                                <span>Gene annotation version:</span> {item.GeneAnnotationVersion}
                            </li>
                            <li>
                                <span>Created by :</span> {item.CreatedBy}
                            </li>
                        </ul>
                    </div>
                ))}
            </div>
        );
    }
}

class StudyOverview extends React.Component {
    constructor(props) {
        super(props);
        this.state = {studyComp: []};
    }

    componentDidMount() {
        fetch(`${URL_PREFIX}/study/${this.props.studyName}`)
            .then(result => result.json())
            .then(study => {
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
                                        <span>Used Samples: </span> {this.countSampleSubset(design.SampleSubset)} of {study.SampleCount}
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

    countSampleSubset(sampleSubset) {
        return sampleSubset.filter(entry => entry.IsUsed).length
    }
}

const App = () => (
    <ErrorBoundary>
        <Router>
            <div>
                <Switch>
                    <Route exact path="/" component={Home}/>
                    <Route path="/study/:study_name" component={SingleStudyView}/>
                    <Route path="/study" component={Home}/>
                    <Route component={NotFound}/>
                </Switch>
            </div>
        </Router>
    </ErrorBoundary>
);

const Home = () => <StudyList/>;
const NotFound = () => <h2>404 - Not Found</h2>;
const SingleStudyView = ({match}) => <StudyOverview studyName={match.params.study_name}/>;

ReactDOM.render(<App/>, document.getElementById('app'));
