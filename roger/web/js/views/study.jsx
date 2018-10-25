import React from 'react';
import ReactDOM from 'react-dom';
import {URL_PREFIX} from "../components/rest";

class StudyOverview extends React.Component {
    constructor() {
        super();
        this.state = { items: [] };
    }

    componentDidMount() {
        fetch(`${URL_PREFIX}/study`)
            .then(result=>result.json())
            .then(items=> {
                this.setState({items: items});
            });
    }

    render() {
        return(
            <div>
                {this.state.items.map(item => (
                    <div key={item.Name} className="study_overview">
                        <p><span>Name:</span> {item.Name}</p>
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

class StudyView extends React.Component {
    render() {
        return (
            <div><StudyOverview /></div>
        );
    }
}

ReactDOM.render(<StudyView />, document.getElementById('study_view'));
