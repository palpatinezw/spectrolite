import React from "react";
import './App.css'
import ImageCropper from "./ImageCropper";
import {dataURLToBlob} from "./auxiliary";
import { getCookie, setCookie } from "./cookies";

const App: React.FC = () => {
    const [pageNo, setPageNo] = React.useState(0);

    const [xMin, setXMin] = React.useState(0);
    const [xWidth, setXWidth] = React.useState(0);
    const [nbCalib, setNbCalib] = React.useState(3);

    const [calibData, setCalibData] = React.useState<{ cropData: any, img: string }[]>([]);
    const [analyseData, setAnalyseData] = React.useState<Array<Number[]>>([]);
    const [calibrationWavelengths, setCalibrationWavelengths] = React.useState<Number[]>([]);

    React.useEffect(() => {
        // Initialize calibData with empty values based on nbCalib
        setCalibData(Array(nbCalib).fill({ cropData: null, img: "" }));
        setAnalyseData(Array(nbCalib).fill([]));
        setCalibrationWavelengths(Array(nbCalib).fill(0));
    }, [nbCalib]);

    React.useEffect(() => {
        let cxMin = getCookie("xMin");
        let cxWidth = getCookie("xWidth");
        if (cxMin) setXMin(parseInt(cxMin));
        if (cxWidth) setXWidth(parseInt(cxWidth));
    }, []);

    return (
        <div className="m-4">
            <h1 className="text-4xl">Spectro</h1>
            <p>Page {pageNo+1}</p>
            {/* 
                0 - Configuration (largueur de reference + nombre de calibration)
                1 - Calibration (images)
                2 - Images a analyser (images)
                3 - Traitements et resultats (images + graphes)
            */}
            {pageNo === 0 && (
                <div className="border p-4 rounded">
                    <h2 className="text-2xl">Configuration</h2>
                    <p>Largeur de reference: {xMin} + {xWidth}</p>
                    <ImageCropper handleResult={(cropData, img) => {
                        setXMin(cropData.x);
                        setXWidth(cropData.width);
                        setCookie("xMin", cropData.x.toString());
                        setCookie("xWidth", cropData.width.toString());
                    }} />
                    <p>Nombre de calibrations: 
                        <input className="border ml-2" type="number" value={nbCalib} onChange={(e) => setNbCalib(parseInt(e.target.value))} />
                    </p> 
                    <br />
                    <button className="btn btn-blue" onClick={() => setPageNo(1)}>
                        Suivant
                    </button>
                </div>
            )}

            {pageNo === 1 && (
                <div className="border p-4 rounded">
                    <h2 className="text-2xl">Calibration</h2>
                    <p>Nombre de calibrations: {nbCalib}</p>

                    {[...Array(nbCalib)].map((_, i) => (
                        <div key={i} className="mb-4 border rounded p-2 bg-gray-200">
                            <h3 className="text-xl">Calibration {i + 1}</h3>
                            <input type="number" value={calibrationWavelengths[i]?.toString() || ""} onChange={(e) => {
                                const newWavelengths = [...calibrationWavelengths];
                                newWavelengths[i] = parseFloat(e.target.value);
                                setCalibrationWavelengths(newWavelengths);
                            }} placeholder="Enter wavelength" className="border p-1 rounded" />
                            <br />
                            <ImageCropper handleResult={(cropData, img) => {
                                const newCalibData = [...calibData];
                                newCalibData[i] = { cropData, img };
                                setCalibData(newCalibData);
                            }} />
                            {calibData[i]?.cropData && (
                                <div className="mt-4 rounded-lg bg-gray-100 p-4">
                                    <h2 className="mb-3 font-semibold">
                                        Crop coordinates
                                    </h2>

                                    <pre className="text-sm">
                                        {JSON.stringify(calibData[i].cropData, null, 2)}
                                    </pre>
                                    <img src={calibData[i].img} alt={`Calibration ${i + 1}`} className="mt-2 max-w-24 h-auto" />
                                    <button className="btn btn-red mt-2" onClick={() => {
                                        let fdata = new FormData();
                                        fdata.append('image', dataURLToBlob(calibData[i].img), "image.png");
                                        fdata.append('xMin', String(xMin));
                                        fdata.append('xWidth', String(xWidth));
                                        fdata.append('yh', String(calibData[i].cropData.y));
                                        fdata.append('yb', String(calibData[i].cropData.y + calibData[i].cropData.height));
                                        fetch('http://localhost:5000/analyse', {    
                                            method: 'POST',
                                            body: fdata
                                        })
                                        .then(response => response.json())
                                        .then(data => {
                                            const newAnalyseData = [...analyseData];
                                            newAnalyseData[i] = data;
                                            setAnalyseData(newAnalyseData);
                                            console.log("New analyse data:", newAnalyseData);
                                        })
                                        .catch(error => console.error('Error:', error));
                                    }}>
                                        Analyse
                                    </button>
                                    {analyseData[i].length > 0 && (
                                        <p className="text-sm mt-2">[✓] Analysed</p>
                                    )}
                                </div>
                            )}
                        </div>
                    ))} 

                    <button className="btn" onClick={() => setPageNo(0)}>
                        Retour
                    </button>
                    <button className="btn btn-blue" onClick={() => setPageNo(2)}>
                        Suivant
                    </button>
                </div>
            )}
        </div>
    )
}

export default App;