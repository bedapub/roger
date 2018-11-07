import React from 'react';

import StudyDrawer from "../components/study/study_drawer";
import StudyOverview from "../components/study/general/overview";

export const SingleStudyView = ({match}) =>
    <StudyDrawer>
        <StudyOverview studyName={match.params.study_name}/>
    </StudyDrawer>;