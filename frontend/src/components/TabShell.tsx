import { useState } from 'react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { cn } from '@/lib/utils'
import DataPanel from './panels/DataPanel'
import ModelsPanel from './panels/ModelsPanel'
import ProgressPanel from './panels/ProgressPanel'

const triggerCls =
  'rounded-t-lg border-b-2 border-transparent px-5 py-3 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground data-[state=active]:border-primary data-[state=active]:bg-background data-[state=active]:text-foreground'

export default function TabShell() {
  const [tab, setTab] = useState('benchmark')

  return (
    <Tabs value={tab} onValueChange={setTab} className="w-full">
      <TabsList className="justify-start gap-2 border-b border-border rounded-none bg-transparent p-0">
        <TabsTrigger value="benchmark" className={cn(triggerCls)}>
          Benchmark
        </TabsTrigger>
        <TabsTrigger value="models" className={cn(triggerCls)}>
          My Models
        </TabsTrigger>
        <TabsTrigger value="sandbox" className={cn(triggerCls)}>
          Sandbox
        </TabsTrigger>
      </TabsList>

      <TabsContent value="benchmark" className="mt-6 animate-in fade-in-0 duration-200">
        <ProgressPanel />
      </TabsContent>
      <TabsContent value="models" className="mt-6 animate-in fade-in-0 duration-200">
        <ModelsPanel />
      </TabsContent>
      <TabsContent value="sandbox" className="mt-6 animate-in fade-in-0 duration-200">
        <DataPanel />
      </TabsContent>
    </Tabs>
  )
}
