'use client';
import Image from "next/image";
import React, { useState } from "react";

const apiLink = "https://us-central1-scriptsearch.cloudfunctions.net/transcript-api"

export default function Home() {
    const [resultsReceived, setResultsReceived] = useState(false);
    const [results, setResults] = useState("");

    const backendConnect = () => {
        let query = document.getElementById("query") as HTMLInputElement;
        let value = query.value;

        let newLink = apiLink + "?request=" + value;

        fetch(newLink).then(response => {
            if (!response.ok) {
                throw new Error("something broke :(");
            }
            return response.json();
        })
            .then(data => {
                console.log(data);
                setResultsReceived(true);
                setResults(data.transcript);
            })
    }

    const handleEnter = (e: { key: string; }) => {
        if (e.key === 'Enter') {
            backendConnect(); 
        }
    }

    return (
        <main className="flex min-h-screen flex-col items-center justify-center p-24">
            {/* <div className="relative flex place-items-center before:absolute before:h-[300px] before:w-full sm:before:w-[480px] before:-translate-x-1/2 before:rounded-full before:bg-gradient-radial before:from-white before:to-transparent before:blur-2xl before:content-[''] after:absolute after:-z-20 after:h-[180px] after:w-full sm:after:w-[240px] after:translate-x-1/3 after:bg-gradient-conic after:from-sky-200 after:via-blue-200 after:blur-2xl after:content-[''] before:dark:bg-gradient-to-br before:dark:from-transparent before:dark:to-blue-700 before:dark:opacity-10 after:dark:from-sky-900 after:dark:via-[#0141ff] after:dark:opacity-40 before:lg:h-[360px] z-[-1]"> */}
            <div className="">    
                {/* <Image
                    className="relative dark:drop-shadow-[0_0_0.3rem_#ffffff70] w-auto h-auto"
                    src="/nextjs-github-pages/Youtube Scripter Logo Big.jpg"
                    alt="Logo"
                    width={180}
                    height={37}
                    priority
                /> */}
                <p className="text-2xl before:content-['ScriptSearch'] before:text-red-500 before:font-bold before:"> - YouTube Transcript Search</p>
            </div>

            {/* <div className="">
                <input type="text" id="link" placeholder="Enter a channel/playlist link" className="border rounded border-gray-500 p-2 my-1 w-80 dark:bg-gray-800 dark:border-gray-600 dark:text-white dark:placeholder-gray-400"></input>
            </div> */}

            <div className="justify-center">
                <input type="text" id="query" placeholder="Enter a video id" onKeyUp={handleEnter} className="border rounded border-gray-500 p-2 w-64 dark:bg-gray-800 dark:border-gray-600 dark:text-white dark:placeholder-gray-400"></input>
                <button id="search" onClick={backendConnect} className="border border-gray-500 rounded py-2  w-16 transition-colors ease-in-out hover:bg-red-600 hover:text-white hover:border-red-700">Submit</button>
            </div>

            {resultsReceived &&
                <div className="my-20 p-1">
                    <p className="font-bold text-xl">Query: {results}</p>
                </div>
            }
        </main>
    );
}
