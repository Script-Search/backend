import Image from "next/image";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="">
        <form>
          <input type="text" name="search" placeholder="Enter a query" className="border rounded border-gray-500 p-2"></input>
          <button className="border border-gray-500 rounded p-2 hover:font-semibold">Submit</button>
        </form>
      </div>
    </main>
  );
}
