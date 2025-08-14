import React from 'react';
import { ClipLoader } from 'react-spinners';

const Spinner = ({ size = 35, color = '#ffffff' }) => {
  return <ClipLoader color={color} size={size} />;
};

export default Spinner;