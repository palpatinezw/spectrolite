import React from "react";
import './App.css'
import ImageCropper from "./ImageCropper";
import {dataURLToBlob} from "./auxiliary";
import { getCookie, setCookie } from "./cookies";
import Plot from "react-plotly.js";

// TODO: replace all FETCH urls with env server url

const App: React.FC = () => {
    const [pageNo, setPageNo] = React.useState(0);

    const [xMin, setXMin] = React.useState(0);
    const [xWidth, setXWidth] = React.useState(0);
    const [nbCalib, setNbCalib] = React.useState(3);

    const [calibData, setCalibData] = React.useState<{ cropData: any, img: string }[]>([]);
    const [analyseData, setAnalyseData] = React.useState<Array<number[]>>([]);
    const [calibrationWavelengths, setCalibrationWavelengths] = React.useState<number[]>([]);
    const [slope, setSlope] = React.useState<number>(0)
    const [intercept, setIntercept] = React.useState<number>(0)

    const [absorbances, setAbsorbances] = React.useState< Array<{name:string, spectre:Array<{longueur:number, absr:number}>}> >([])
    const [blancData, setBlancData] = React.useState< number[] >([])
    const [solutionData, setSolutionData] = React.useState< number[] >([])
    const [solutionName, setSolutionName] = React.useState<string>("")

    const pixelToLongueur = React.useCallback((pixel:number) => {
        return slope*pixel + intercept
    }, [slope, intercept])

    React.useEffect(() => {
        // Initialize calibData with empty values based on nbCalib
        setCalibData(Array(nbCalib).fill({ cropData: null, img: "" }));
        setAnalyseData(Array(nbCalib).fill([]));
        setCalibrationWavelengths(Array(nbCalib).fill(0));
    }, [nbCalib]);

    React.useEffect(() => {
        let cxMin = getCookie("xMin");
        let cxWidth = getCookie("xWidth")
        let cSlope = getCookie("slope")
        let cIntercept = getCookie("intercept")
        if (cxMin) setXMin(parseInt(cxMin));
        if (cxWidth) setXWidth(parseInt(cxWidth));
        if (cSlope) setSlope(Number(cSlope))
        if (cIntercept) setIntercept(Number(cIntercept))
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
                    <p>Astuce: Toutes les images doivent avoir les mêmes dimensions que l'image de configuration.</p>
                    {[...Array(nbCalib)].map((_, i) => (
                        <div key={i} className="mb-4 border rounded p-2 bg-gray-200">
                            <h3 className="text-xl">Calibration {i + 1}</h3>
                            Longueur d'onde: <input type="number" value={calibrationWavelengths[i]?.toString() || ""} onChange={(e) => {
                                const newWavelengths = [...calibrationWavelengths];
                                newWavelengths[i] = parseFloat(e.target.value);
                                setCalibrationWavelengths(newWavelengths);
                            }} placeholder="Enter wavelength" className="border p-1 rounded" />
                            <br />
                            <ImageCropper handleResult={(cropData, img) => {
                                const newCalibData = [...calibData];
                                newCalibData[i] = { cropData, img };
                                setCalibData(newCalibData);
                                const newAnalyseData = [...analyseData]
                                newAnalyseData[i] = []
                                setAnalyseData(newAnalyseData)
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
                                        fetch(`${import.meta.env.VITE_SERVER_URL}/analyse`, {    
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
                                        .catch((error) => {console.error('Error:', error); alert("Erreur lors de l'analyse de l'image. Veuillez réessayer.")});
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

                    <button className="btn btn-blue mb-5" onClick={() => {
                        fetch(`${import.meta.env.VITE_SERVER_URL}/calibration`, {
                            method:"POST", 
                            headers:{
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({
                                intensities: analyseData[0].map((_, i) =>
                                    analyseData.reduce((sum, row) => sum + row[i], 0)
                                ),
                                longueurs: calibrationWavelengths
                            })
                        }).then((res) => {
                            return res.json()
                        }).then((data) => {
                            setSlope(data.slope)
                            setIntercept(data.intercept)
                            setCookie("slope", data.slope)
                            setCookie("intercept", data.intercept)
                        }).catch((error) => {
                            console.error('Error:', error);
                            alert("Erreur lors de la calibration. Veuillez réessayer.");
                        });
                    }}>Calibrate</button>
                    {slope != 0 && 
                        <div className="border rounded mb-5">
                            y = {slope} * x + {intercept}
                        </div>
                    }

                    <hr />

                    <button className="btn" onClick={() => setPageNo(0)}>
                        Retour
                    </button>
                    <button className="btn btn-blue" onClick={() => setPageNo(2)}>
                        Suivant
                    </button>
                </div>
            )}

            {pageNo === 2 && (
                <div className="border p-4 rounded">
                    <h2 className="text-2xl">Analyse</h2>
                    <div className="flex md:flex-row flex-col">
                        <div className="flex-1">
                            <p className="text-l">BLANC</p>
                            <ImageCropper handleResult={(cropData, img) => {
                                let fdata = new FormData();
                                fdata.append('image', dataURLToBlob(img), "blanc.png");
                                fdata.append('xMin', String(xMin));
                                fdata.append('xWidth', String(xWidth));
                                fdata.append('yh', String(cropData.y));
                                fdata.append('yb', String(cropData.y + cropData.height));
                                fetch(`${import.meta.env.VITE_SERVER_URL}/analyse`, {    
                                    method: 'POST',
                                    body: fdata
                                })
                                .then(response => response.json())
                                .then(data => {
                                    setBlancData(data);
                                    console.log("New blanc data:", data);
                                })
                                .catch((error) => {
                                    console.error('Error:', error);
                                    alert("Erreur lors de l'analyse de l'image. Veuillez réessayer.");
                                });
                            }}/>
                            {blancData.length > 0 && <p className="text-sm mt-2">[✓] Analysed</p>}
                        </div>
                        <div className="flex-1">
                            <p className="text-l">SOLUTION</p>
                            <ImageCropper handleResult={(cropData, img) => {
                                let fdata = new FormData();
                                fdata.append('image', dataURLToBlob(img), "blanc.png");
                                fdata.append('xMin', String(xMin));
                                fdata.append('xWidth', String(xWidth));
                                fdata.append('yh', String(cropData.y));
                                fdata.append('yb', String(cropData.y + cropData.height));
                                fetch(`${import.meta.env.VITE_SERVER_URL}/analyse`, {    
                                    method: 'POST',
                                    body: fdata
                                })
                                .then(response => response.json())
                                .then(data => {
                                    setSolutionData(data);
                                    console.log("New solution data:", data);
                                })
                                .catch((error) => {
                                    console.error('Error:', error);
                                    alert("Erreur lors de l'analyse de l'image. Veuillez réessayer.");
                                });
                            }}/>
                            {solutionData.length > 0 && <p className="text-sm mt-2">[✓] Analysed</p>}
                        </div>
                    </div>

                    <input type="text" placeholder="Nom de la solution" value={solutionName} onChange={(e) => setSolutionName(e.target.value)} className="border p-1 rounded mt-2" />

                    <button className="btn btn-blue mb-5 mt-5" onClick={() => {
                        if (solutionName === "" || blancData.length === 0 || solutionData.length === 0) {
                            alert("Veuillez remplir tous les champs avant d'analyser. Si une image est en cours d'analyse, veuillez attendre la fin de l'analyse.");
                            return;
                        }
                        let tempAbsr = [...absorbances]
                        tempAbsr.push({
                            name: solutionName,
                            spectre: solutionData.map((absr, i) => ({
                                longueur: pixelToLongueur(i),
                                absr: -Math.log10(absr/blancData[i])
                            }))
                        })
                        setAbsorbances(tempAbsr)
                        setSolutionName("")
                        setBlancData([])
                        setSolutionData([])
                        console.log("Absorbances:", tempAbsr)
                    }}>
                        Analyser
                    </button>

                    <hr />

                    <div className="mb-5">
                        <h2 className="text-2xl">Spectres</h2>
                        {absorbances.map((abs, i) => (
                            <div key={i} className="mb-4 border rounded p-2 bg-gray-200 flex justify-between items-center">
                                <h3 className="text-xl">{abs.name}</h3>
                                <button className="btn" onClick={() => {
                                    const csvContent = "data:text/csv;charset=utf-8," + abs.spectre.map(e => `${e.longueur},${e.absr}`).join("\n");
                                    const encodedUri = encodeURI(csvContent);
                                    const link = document.createElement("a");
                                    link.setAttribute("href", encodedUri);
                                    link.setAttribute("download", `${abs.name}.csv`);
                                    document.body.appendChild(link); // Required for FF
                                    link.click();
                                    document.body.removeChild(link);
                                }}>
                                    CSV
                                </button>
                            </div>
                        ))}
                    </div>

                    <hr/>

                    <button className="btn mt-2" onClick={() => setPageNo(1)}>
                        Retour
                    </button>
                    <button className="btn btn-blue" onClick={() => setPageNo(3)}>
                        Suivant
                    </button>
                </div>
            )}

            {pageNo === 3 && (
                <div className="border p-4 rounded">
                    <h2 className="text-2xl">Resultats</h2>
                    <Plot
                        data={absorbances.map(abs => ({
                            x: abs.spectre.map(point => point.longueur),
                            y: abs.spectre.map(point => point.absr),
                            type: 'scatter',
                            mode: 'lines',
                            name: abs.name,
                        }))}
                        layout={{ title: 'Spectres d\'absorbance', xaxis: { title: 'Longueur d\'onde (nm)' }, yaxis: { title: 'Absorbance' } }}
                    />
                    <br />
                    <button className="btn mt-2" onClick={() => setPageNo(2)}>
                        Retour
                    </button>
                </div>
            )}
        </div>
    )
}

export default App;