import React, { useState, createRef } from "react";
import Cropper from "react-cropper";
import type {ReactCropperElement} from "react-cropper";
import "cropperjs/dist/cropper.css";
import './App.css'

interface CropData {
  x: number;
  y: number;
  width: number;
  height: number;
}

const ImageCropper: React.FC<{ handleResult: (cropData: CropData, img: string) => void }> = ({ handleResult }) => {
  const [image, setImage] = useState<string>("");
  const [cropData, setCropData] = useState<CropData | null>(null);

  const cropperRef = createRef<ReactCropperElement>();

  /*
   * Upload image
   */
  const onChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;

    if (!files || files.length === 0) {
      return;
    }

    const reader = new FileReader();

    reader.onload = () => {
      setImage(reader.result as string);
      setCropData(null);
    };

    reader.readAsDataURL(files[0]);
  };

  /*
   * Extract crop coordinates
   */
  const getCropData = () => {
    const cropper = cropperRef.current?.cropper;

    if (!cropper) {
      return;
    }

    const data = cropper.getData(true);

    const result: CropData = {
      x: data.x,
      y: data.y,
      width: data.width,
      height: data.height,
    };

    setCropData(result);

    handleResult(result, image);
    setImage(""); // Clear the image after getting crop data
    setCropData(null); // Clear the crop data after getting crop data

    console.log("Crop coordinates:", result);
  };

  return (
    <div className="mx-auto w-full max-w-4xl p-6">

      {/* Image upload */}
      <div className="mb-6">
        <input
          type="file"
          accept="image/*"
          onChange={onChange}
          className="block text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 focus:outline-none"
        />
      </div>

      {/* Cropper */}
      {image && (
        <>
          <div className="
                mx-auto
                h-[60vh]
                max-h-[600px]
                min-h-[300px]
                w-full
                max-w-[1000px]
            ">
            <Cropper
              ref={cropperRef}
              src={image}

              style={{
                height: "100%",
                width: "100%",
              }}

              /*
               * No aspect ratio:
               * the user can freely resize the crop box.
               */
              viewMode={1}

              minCropBoxWidth={10}
              minCropBoxHeight={10}
              autoCrop = {false}

              background={false}
              responsive={true}
              guides={true}

              movable={true}
              cropBoxMovable={true}
              cropBoxResizable={true}

              checkOrientation={false}
            />
          </div>

          {/* Extract coordinates */}
          <button
            className="btn btn-blue mt-4"
            type="button"
            onClick={getCropData}
          >
            Confirm
          </button>

          {/* Display coordinates */}
          {/* {cropData && (
            <div className="mt-4 rounded-lg bg-gray-100 p-4">
              <h2 className="mb-3 font-semibold">
                Crop coordinates
              </h2>

              <pre className="text-sm">
                {JSON.stringify(cropData, null, 2)}
              </pre>
            </div>
          )} */}
        </>
      )}
    </div>
  );
};

export default ImageCropper;