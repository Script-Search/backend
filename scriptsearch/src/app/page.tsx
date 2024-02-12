'use client';
import Image from "next/image";
import React, {useState} from "react";

const apiLink = "https://us-central1-script-search-414110.cloudfunctions.net/transcript-api"

const backendConnect = () => {
  const headers = {'Content-Type':'application/json',
  'Access-Control-Allow-Origin':'*',
  'Access-Control-Allow-Methods':'POST,PATCH,OPTIONS'}

  let input = document.getElementById("query") as HTMLInputElement;
  let value = input.value;

  let newLink = apiLink + "?request=" + value;
  console.log(newLink);

  fetch(newLink).then(response => {
    if(!response.ok){
      throw new Error("Error");
    }
    return response.json();
  })
  .then(data => {
    console.log(data);
  })
}

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="relative flex place-items-center before:absolute before:h-[300px] before:w-full sm:before:w-[480px] before:-translate-x-1/2 before:rounded-full before:bg-gradient-radial before:from-white before:to-transparent before:blur-2xl before:content-[''] after:absolute after:-z-20 after:h-[180px] after:w-full sm:after:w-[240px] after:translate-x-1/3 after:bg-gradient-conic after:from-sky-200 after:via-blue-200 after:blur-2xl after:content-[''] before:dark:bg-gradient-to-br before:dark:from-transparent before:dark:to-blue-700 before:dark:opacity-10 after:dark:from-sky-900 after:dark:via-[#0141ff] after:dark:opacity-40 before:lg:h-[360px] z-[-1]">
        <Image
          className="relative dark:drop-shadow-[0_0_0.3rem_#ffffff70] dark:invert"
          src="/Youtube Scripter Logo Big.jpg"
          alt="Logo"
          width={180}
          height={37}
          priority
        />
      </div>

      <div className="">
        <input type="text" id="query" placeholder="Enter a query" className="border rounded border-gray-500 p-2"></input>
        <button id="search" onClick={backendConnect} className="border border-gray-500 rounded p-2 hover:font-semibold">Submit</button>
      </div>
    </main>
  );
}
