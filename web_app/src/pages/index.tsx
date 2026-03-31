import Head from 'next/head';

import { PrototypeShell } from '@/components/prototype/PrototypeShell';

export default function HomePage() {
  return (
    <>
      <Head>
        <title>My Platform</title>
        <meta name="description" content="Trading intelligence workspace." />
      </Head>
      <PrototypeShell />
    </>
  );
}
