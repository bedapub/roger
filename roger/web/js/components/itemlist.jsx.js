import React from "react";

export default class ItemLister extends React.Component {
    constructor() {
        super();
        this.state = { items: [] };
    }

    componentDidMount() {
        fetch(`http://rkalbhpc002.kau.roche.com:5000/api/study`)
            .then(result=>result.json())
            .then(items=> {
                this.setState({items: items});
            });
    }

    render() {
        return(
            <div>
                <ul>
                    {this.state.items.map(item => (
                        <li key={item.Name}>
                            Name: {item.Name}
                        </li>
                    ))}
                </ul>
            </div>
        );
    }
}