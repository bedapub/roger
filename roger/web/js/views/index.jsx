import React from 'react';
import ReactDOM from 'react-dom';
import {URL_PREFIX} from "../components/rest";

class StudyList extends React.Component {
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
                        <p><span>Name:</span> {item.Name} <Link to='/href' >ASD</Link> </p>
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

class IndexView extends React.Component {
    render() {
        return (
            <div><StudyList /></div>
        );
    }
}

ReactDOM.render(<IndexView />, document.getElementById('index_view'));
