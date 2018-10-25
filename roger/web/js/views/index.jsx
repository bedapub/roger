import React from 'react';
import ReactDOM from 'react-dom';
import ItemLister from "../components/itemlist.jsx";

class IndexView extends React.Component {
    render() {
        return (
            <div><ItemLister /></div>
        );
    }
}

ReactDOM.render(<IndexView />, document.getElementById('index_view'));
