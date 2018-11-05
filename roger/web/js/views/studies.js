import React from 'react';
import {URL_PREFIX} from "../logic/rest";
import {Link} from "react-router-dom";
import "isomorphic-fetch"

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

export const StudiesView = () => <StudyList/>;