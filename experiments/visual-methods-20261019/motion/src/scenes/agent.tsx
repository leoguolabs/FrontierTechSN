import { makeScene2D, Node, Rect, Txt, Line, Circle } from '@motion-canvas/2d'
import {
  all,
  chain,
  createRef,
  createSignal,
  easeInOutCubic,
  easeOutCubic,
  waitFor,
} from '@motion-canvas/core'
const ink = '#143c3b',
  muted = '#657c73',
  green = '#3e8877',
  orange = '#d96738',
  paper = '#f2f0e9'
export default makeScene2D(function* (view) {
  view.fill(paper)
  view.add(
    <>
      <Txt
        text="BYTEFRONT / MECHANISM NOTES"
        x={-505}
        y={-450}
        fill={ink}
        fontSize={25}
        fontFamily="Arial"
        letterSpacing={3}
      />
      <Line
        points={[
          [-864, -400],
          [864, -400],
        ]}
        stroke={ink}
        lineWidth={2}
      />
      <Txt
        text="THE AGENT LOOP"
        x={675}
        y={-450}
        fill={muted}
        fontSize={25}
        fontFamily="Arial"
      />
    </>,
  )
  const headline = createRef<Txt>()
  view.add(
    <Txt
      ref={headline}
      text="A useful answer."
      x={0}
      y={-280}
      fill={ink}
      fontFamily="Arial"
      fontWeight={700}
      fontSize={112}
      opacity={0}
    />,
  )
  const s1 = createRef<Node>(),
    model = createRef<Rect>(),
    answer = createRef<Rect>(),
    wire = createRef<Line>()
  view.add(
    <Node ref={s1}>
      <Rect
        ref={model}
        x={-580}
        y={85}
        width={360}
        height={250}
        radius={36}
        fill={ink}
        scale={0}
      >
        <Txt
          text="MODEL"
          fill={paper}
          fontSize={58}
          fontFamily="Arial"
          fontWeight={700}
        />
      </Rect>
      <Line
        ref={wire}
        points={[
          [-390, 85],
          [125, 85],
        ]}
        stroke={green}
        lineWidth={7}
        endArrow
        arrowSize={22}
        end={0}
      />
      <Rect
        ref={answer}
        x={450}
        y={85}
        width={590}
        height={330}
        radius={32}
        stroke={green}
        lineWidth={3}
        fill="#fffdf5"
        opacity={0}
      >
        <Txt
          text={'One way\nforward.'}
          fill={ink}
          fontSize={76}
          fontFamily="Arial"
          fontWeight={600}
          lineHeight={88}
        />
      </Rect>
      <Txt
        fontFamily="Arial"
        text="Information to begin with."
        x={0}
        y={365}
        fill={muted}
        fontSize={36}
      />
    </Node>,
  )
  yield* all(
    headline().opacity(1, 1),
    headline().y(-295, 1),
    model().scale(1, 1, easeOutCubic),
  )
  yield* wire().end(1, 1.2, easeInOutCubic)
  yield* all(answer().opacity(1, 0.8), answer().x(400, 0.8, easeOutCubic))
  yield* waitFor(3)
  // 6s: move the response out; introduce the operation and its physical path.
  const s2 = createRef<Node>(),
    tool = createRef<Circle>(),
    flow = createRef<Line>(),
    dot = createRef<Circle>()
  view.add(
    <Node ref={s2} opacity={0}>
      <Circle x={-560} y={90} width={230} height={230} fill={green}>
        <Txt fontFamily="Arial" text="GOAL" fill={paper} fontSize={48} />
      </Circle>
      <Line
        ref={flow}
        points={[
          [-435, 90],
          [-180, 90],
          [-180, -20],
          [190, -20],
        ]}
        stroke={green}
        lineWidth={7}
        radius={48}
        endArrow
        arrowSize={22}
        end={0}
      />
      <Circle
        ref={tool}
        x={390}
        y={90}
        width={340}
        height={340}
        stroke={orange}
        lineWidth={7}
        fill="#fff8e9"
        scale={0.6}
      >
        <Txt
          fontFamily="Arial"
          text="TOOL"
          fill={ink}
          fontSize={68}
          fontWeight={700}
        />
      </Circle>
      <Circle
        ref={dot}
        x={-430}
        y={90}
        width={26}
        height={26}
        fill={orange}
        opacity={0}
      />
      <Txt
        fontFamily="Arial"
        text="An operation carries the goal into the world."
        y={365}
        fill={muted}
        fontSize={36}
      />
    </Node>,
  )
  yield* all(
    s1().opacity(0, 0.75),
    s1().x(-120, 0.75),
    s2().opacity(1, 0.75),
    headline().text('An agent takes action.', 0.75),
  )
  yield* tool().scale(1, 0.75, easeOutCubic)
  yield* all(
    flow().end(1, 1.5, easeInOutCubic),
    chain(
      dot().opacity(1, 0.1),
      dot().position([190, -20], 1.4, easeInOutCubic),
    ),
  )
  yield* waitFor(3)
  // 12s: expose three nodes in a spatial mechanism, with evidence appearing last.
  const s3 = createRef<Node>(),
    links = createRef<Line>()
  const nodes = [createRef<Rect>(), createRef<Rect>(), createRef<Rect>()]
  view.add(
    <Node ref={s3} opacity={0}>
      <Line
        ref={links}
        points={[
          [-570, 90],
          [570, 90],
        ]}
        stroke={green}
        lineWidth={5}
        end={0}
      />
      {['Read a goal', 'Use a tool', 'Check the result'].map((s, i) => (
        <Rect
          ref={nodes[i]}
          x={-570 + i * 570}
          y={90}
          width={460}
          height={310}
          fill={i === 2 ? '#dbe9d9' : '#fffdf5'}
          stroke={green}
          lineWidth={3}
          radius={24}
          scale={0.8}
          opacity={0}
        >
          <Txt
            fontFamily="Arial"
            text={'0' + (i + 1)}
            y={-72}
            fill={orange}
            fontSize={80}
            fontWeight={700}
          />
          <Txt fontFamily="Arial" text={s} y={65} fill={ink} fontSize={44} />
        </Rect>
      ))}
      <Txt
        fontFamily="Arial"
        text="A goal, an operation, and observable evidence."
        y={365}
        fill={muted}
        fontSize={36}
      />
    </Node>,
  )
  yield* all(
    s2().opacity(0, 0.75),
    s3().opacity(1, 0.75),
    headline().text('Inspect each step.', 0.75),
  )
  yield* all(
    links().end(1, 2.25),
    chain(
      ...nodes.map((r) =>
        all(r().opacity(1, 0.75), r().scale(1, 0.75, easeOutCubic)),
      ),
    ),
  )
  yield* waitFor(3)
  // 18s: the missing return path closes, then a signal travels back into action.
  const s4 = createRef<Node>(),
    loop = createRef<Line>(),
    signal = createRef<Circle>()
  view.add(
    <Node ref={s4} opacity={0}>
      <Line
        ref={loop}
        points={[
          [-520, -30],
          [520, -30],
          [520, 250],
          [-520, 250],
          [-520, -30],
        ]}
        radius={100}
        stroke={green}
        lineWidth={9}
        endArrow
        arrowSize={24}
        end={0}
      />
      {[
        ['Action', -520, -30],
        ['Feedback', 520, -30],
        ['Correction', 0, 250],
      ].map(([s, a, b]) => (
        <Rect
          x={a as number}
          y={b as number}
          width={370}
          height={135}
          fill={paper}
          radius={24}
        >
          <Txt
            fontFamily="Arial"
            text={s as string}
            fontSize={54}
            fill={ink}
            fontWeight={600}
          />
        </Rect>
      ))}
      <Circle
        ref={signal}
        x={-520}
        y={-30}
        width={28}
        height={28}
        fill={orange}
        opacity={0}
      />
      <Txt
        fontFamily="Arial"
        text="The next attempt uses what the last one revealed."
        y={410}
        fill={muted}
        fontSize={34}
      />
    </Node>,
  )
  yield* all(
    s3().opacity(0, 0.75),
    s4().opacity(1, 0.75),
    headline().text('Feedback closes the loop.', 0.75),
  )
  yield* loop().end(1, 2.25, easeInOutCubic)
  yield* all(
    signal().opacity(1, 0.1),
    chain(
      signal().position([520, -30], 0.4),
      signal().position([520, 250], 0.25),
      signal().position([-520, 250], 0.55),
      signal().position([-520, -30], 0.3),
    ),
  )
  yield* waitFor(1.5)
})
