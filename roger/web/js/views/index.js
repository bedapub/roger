import React from 'react';
import ReactDOM from 'react-dom';
import {BrowserRouter as Router, Route, Link, Switch} from "react-router-dom";

import {URL_PREFIX} from "../components/rest";


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
                    <div key={item.Name} className="study_overview">
                        <p><span>Name:</span> <Link to={`/study/${item.Name}`}>{item.Name}</Link> </p>
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

const App = () => (
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
);

const Home = () => <StudyList/>;
const NotFound = () => <h2>404 - Not Found</h2>;
const SingleStudyView = ({match}) => <h3>Requested Study: {match.params.study_name}</h3>;

ReactDOM.render(<App/>, document.getElementById('app'));
