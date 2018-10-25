import React from 'react';
import ReactDOM from 'react-dom';
import ItemLister from "../components/itemlist.jsx";

class StudyView extends React.Component {
    render() {
        return (
            <div><ItemLister /></div>
        );
    }
}

ReactDOM.render(<StudyView />, document.getElementById('study_view'));
